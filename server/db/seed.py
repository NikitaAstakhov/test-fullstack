import os
import logging
import random
import asyncio
from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from .models import metadata, submissions
from app.tracing import OpenTelemetryAsyncTrace, TraceFeatures

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SubmissionSeeder:

    def __init__(
        self,
        database_url: str,
        target_count: int = 2_000_000,
        batch_size: int = 1_000,
        threshold: int = 100_000,
        max_workers: int | None = None
    ):
        self.database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        self.target_count = target_count
        self.batch_size = batch_size
        self.threshold = threshold

        if max_workers is None:
            cores = os.cpu_count() or 1
            self.max_workers = cores * 5
        else:
            self.max_workers = max_workers

        logger.info(
            f"Initialized SubmissionSeeder(target_count={self.target_count}, "
            f"batch_size={self.batch_size}, threshold={self.threshold}, "
            f"max_workers={self.max_workers})"
        )

        self.engine: AsyncEngine = create_async_engine(self.database_url, echo=False)

        self.first_names = [
            "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
            "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
            "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
            "Matthew", "Margaret", "Anthony", "Betty", "Donald", "Sandra", "Mark", "Ashley",
            "Paul", "Dorothy", "Steven", "Kimberly", "Andrew", "Emily", "Kenneth", "Donna",
            "George", "Michelle", "Joshua", "Carol", "Kevin", "Amanda", "Brian", "Melissa",
            "Edward", "Deborah",
        ]
        self.last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
            "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
            "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
            "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
            "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
            "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
            "Carter", "Roberts",
        ]

        self.start_date = date.today() - timedelta(days=365)

    async def get_estimated_count(self) -> int:
        async with OpenTelemetryAsyncTrace(
            name="seed.get_estimated_count",
            op="seed.db",
            features=TraceFeatures.SPAN | TraceFeatures.METRICS,
        ):
            try:
                async with self.engine.connect() as conn:
                    stmt = text(
                        "SELECT reltuples::BIGINT AS estimate "
                        "FROM pg_class WHERE oid = 'submissions'::regclass"
                    )
                    result = await conn.execute(stmt)
                    estimate = result.scalar_one_or_none()
                    est_val = int(estimate or 0)
                    logger.info(f"Approximate count fetched: {est_val}")
                    return est_val
            except SQLAlchemyError as e:
                logger.error(f"Failed to fetch approximate count: {e}")
                return 0

    async def generate_batch(self) -> list[dict]:
        batch = []
        for _ in range(self.batch_size):
            fn = random.choice(self.first_names)
            ln = random.choice(self.last_names)
            random_days = random.randint(0, 364)
            dt = self.start_date + timedelta(days=random_days)
            batch.append({"date": dt, "first_name": fn, "last_name": ln})
        return batch

    async def insert_batch(self, records: list[dict]) -> None:
        try:
            async with self.engine.begin() as conn:
                await conn.execute(submissions.insert(), records)
            logger.debug(f"Inserted batch of {len(records)} records")
        except SQLAlchemyError as e:
            logger.error(f"Failed to insert batch: {e}")
            raise

    async def run(self) -> None:
        async with OpenTelemetryAsyncTrace(
            name="seed.run",
            op="seed",
            features=TraceFeatures.TRANSACTION | TraceFeatures.METRICS,
        ):
            logger.info("Starting seeding process")

            async with self.engine.begin() as conn:
                await conn.run_sync(lambda sync_conn: metadata.create_all(sync_conn))
            logger.info("Ensured submissions table exists")

            estimate = await self.get_estimated_count()
            logger.info(f"Estimated count is {estimate}")

            if estimate >= self.threshold:
                logger.info(
                    f"Count ({estimate}) >= threshold ({self.threshold}); skipping seeding."
                )
                await self.engine.dispose()
                return

            remaining = max(self.target_count - estimate, 0)
            total_batches = remaining // self.batch_size
            if remaining % self.batch_size:
                total_batches += 1

            logger.info(
                f"Seeding up to {self.target_count} records "
                f"({total_batches} batches of ~{self.batch_size} records)..."
            )

            async with OpenTelemetryAsyncTrace(
                name="seed.insert_batches",
                op="seed.db.insert",
                features=TraceFeatures.SPAN | TraceFeatures.METRICS | TraceFeatures.OBJGRAPH,
            ):
                semaphore = asyncio.Semaphore(self.max_workers)
                tasks = []

                async def sem_insert():
                    async with semaphore:
                        batch = await self.generate_batch()
                        await self.insert_batch(batch)

                for _ in range(total_batches):
                    tasks.append(asyncio.create_task(sem_insert()))

                await asyncio.gather(*tasks)

            logger.info("Seeding complete.")

            self.first_names = None
            self.last_names = None
            await self.engine.dispose()
            logger.info("Cleaned up engine and cleared name pools.")

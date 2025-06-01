import logging
import datetime
from typing import List, Dict, Any

from sqlalchemy import select, and_, desc, func
from databases import Database
from opentelemetry import trace

from .models import submissions
from app.tracing import OpenTelemetryAsyncTrace, TraceFeatures

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

tracer = trace.get_tracer(__name__)


async def insert_submission(
    db: Database, *, date: datetime.date, first_name: str, last_name: str
) -> int:
    with tracer.start_as_current_span("crud.insert_submission") as span:
        span.set_attribute("first_name", first_name)
        span.set_attribute("last_name", last_name)
        span.set_attribute("date", date.isoformat())
        query = submissions.insert().values(
            date=date,
            first_name=first_name,
            last_name=last_name,
        )
        try:
            row_id = await db.execute(query)
            logger.info(f"Inserted submission id={row_id}")
            return row_id
        except Exception as e:
            logger.error(f"Error inserting submission: {e}")
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise


async def get_history(db: Database) -> List[Dict[str, Any]]:
    async with OpenTelemetryAsyncTrace(
        name="crud.get_history",
        op="crud",
        features=TraceFeatures.SPAN | TraceFeatures.METRICS,
    ):
        logger.info("Fetching last 10 submissions with prior-count")
        s1 = submissions.alias("s1")
        s2 = submissions.alias("s2")

        subq = (
            select(func.count())
            .select_from(s2)
            .where(
                and_(
                    s2.c.first_name == s1.c.first_name,
                    s2.c.last_name == s1.c.last_name,
                    s2.c.date < s1.c.date,
                )
            )
            .correlate(s1)
            .scalar_subquery()
        )

        main_q = (
            select(
                s1.c.date,
                s1.c.first_name,
                s1.c.last_name,
                subq.label("count"),
            )
            .order_by(desc(s1.c.date), s1.c.first_name, s1.c.last_name)
            .limit(10)
        )

        try:
            rows = await db.fetch_all(main_q)
        except Exception as e:
            logger.error(f"Error fetching history: {e}")
            raise

        results = []
        for row in rows:
            results.append(
                {
                    "date": row["date"].isoformat(),
                    "first_name": row["first_name"],
                    "last_name": row["last_name"],
                    "count": int(row["count"]),
                }
            )

        logger.info(f"Returning {len(results)} history records")
        return results

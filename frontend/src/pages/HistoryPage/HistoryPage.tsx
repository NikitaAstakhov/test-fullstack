import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import styles from "./HistoryPage.module.scss";
import Spinner from "@components/Spinner/Spinner";
import { fetchHistory } from "@services/api";
import { HistoryRecord } from "@services/dataTypes";

const HistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const [historyData, setHistoryData] = useState<HistoryRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadHistory = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchHistory();
        setHistoryData(data);
      } catch (err) {
        console.error("Error fetching history:", err);
        setError("Не удалось получить историю. Попробуйте позже.");
      } finally {
        setLoading(false);
      }
    };

    loadHistory();
  }, []);

  return (
    <div className={`container ${styles.historyContainer}`}>
      <button
        className={styles.backButton}
        onClick={() => navigate("/")}
        aria-label="Back to home"
      >
        ←
      </button>
      <h1 className={styles.title}>История успешных отправок</h1>

      {loading && <Spinner />}

      {!loading && error && <div className={styles.errorMsg}>{error}</div>}

      {!loading && !error && historyData.length > 0 && (
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Дата</th>
              <th>Имя</th>
              <th>Фамилия</th>
              <th>Count</th>
            </tr>
          </thead>
          <tbody>
            {historyData.map((rec, idx) => (
              <tr key={idx}>
                <td>{rec.date}</td>
                <td>{rec.first_name}</td>
                <td>{rec.last_name}</td>
                <td>{rec.count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {!loading && !error && historyData.length === 0 && (
        <div className={styles.empty}>Нет данных для отображения.</div>
      )}
    </div>
  );
};

export default HistoryPage;

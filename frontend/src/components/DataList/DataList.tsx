import React from "react";
import styles from "./DataList.module.scss";

interface DataListProps {
  items: Array<{ date: string; name: string }>;
}

const DataList: React.FC<DataListProps> = ({ items }) => {
  if (items.length === 0) {
    return <div className={styles.emptyMessage}>Нет данных для отображения.</div>;
  }

  return (
    <table className={styles.table}>
      <thead>
        <tr>
          <th>Дата</th>
          <th>Имя</th>
        </tr>
      </thead>
      <tbody>
        {items.map((item, idx) => (
          <tr key={idx}>
            <td>{item.date}</td>
            <td>{item.name}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default DataList;

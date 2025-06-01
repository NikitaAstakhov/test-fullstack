import React from "react";
import { Link } from "react-router-dom";
import styles from "./HomePage.module.scss";

const HomePage: React.FC = () => {
  return (
    <div className={`container ${styles.homeContainer}`}>
      <h1 className={styles.title}>Добро пожаловать</h1>
      <nav className={styles.nav}>
        <Link className={styles.link} to="/submit">
          Перейти на страницу отправки формы
        </Link>
        <Link className={styles.link} to="/history">
          Перейти на страницу истории
        </Link>
      </nav>
    </div>
  );
};

export default HomePage;
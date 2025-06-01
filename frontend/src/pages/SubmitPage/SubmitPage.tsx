import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import styles from "./SubmitPage.module.scss";
import Spinner from "@components/Spinner/Spinner";
import DataList from "@components/DataList/DataList";
import { submitForm } from "@services/api";
import { FormPayload, SubmitErrorResponse } from "@services/dataTypes";
import { parseQueryString, buildQueryString } from "@utils/queryString";

const SubmitPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const [date, setDate] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");

  const [errors, setErrors] = useState<Record<string, string[]>>({});

  const [dataList, setDataList] = useState<
    Array<{ date: string; name: string }>
  >([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const queryParams = parseQueryString(location.search);
    if (
      queryParams.date &&
      queryParams.first_name &&
      queryParams.last_name
    ) {
      setDate(queryParams.date);
      setFirstName(queryParams.first_name);
      setLastName(queryParams.last_name);

      handleSubmit({
        date: queryParams.date,
        first_name: queryParams.first_name,
        last_name: queryParams.last_name,
      });
    }
  }, []);

  const handleSubmit = async (overridePayload?: FormPayload) => {
    const payload: FormPayload = overridePayload
      ? overridePayload
      : {
          date: date,
          first_name: firstName,
          last_name: lastName,
        };

    setLoading(true);
    setErrors({});
    setDataList([]);

    try {
      const response = await submitForm(payload);
      setDataList(response.data);

      const qs = buildQueryString({
        date: payload.date,
        first_name: payload.first_name,
        last_name: payload.last_name,
      });
      navigate(`/submit?${qs}`, { replace: true });
    } catch (err) {
      if (
        typeof err === "object" &&
        err !== null &&
        "success" in (err as any) &&
        !(err as SubmitErrorResponse).success
      ) {
        const errResp = err as SubmitErrorResponse;
        setErrors(errResp.error);
      } else {
        console.error("Unexpected error in submitForm:", err);
      }
    } finally {
      setLoading(false);
    }
  };

  const onFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSubmit();
  };

  return (
    <div className={`container ${styles.submitContainer}`}>
      <button
        className={styles.backButton}
        onClick={() => navigate("/")}
        aria-label="Back to home"
      >
        ←
      </button>
      <h1 className={styles.title}>Отправка формы</h1>

      <form className={styles.form} onSubmit={onFormSubmit}>
        <div className={styles.fieldGroup}>
          <label htmlFor="date">Дата:</label>
          <input
            id="date"
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
          {errors.date &&
            errors.date.map((msg, i) => (
              <div key={i} className={styles.error}>
                {msg}
              </div>
            ))}
        </div>

        <div className={styles.fieldGroup}>
          <label htmlFor="firstName">Имя:</label>
          <input
            id="firstName"
            type="text"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            placeholder="Введите имя"
          />
          {errors.first_name &&
            errors.first_name.map((msg, i) => (
              <div key={i} className={styles.error}>
                {msg}
              </div>
            ))}
        </div>

        <div className={styles.fieldGroup}>
          <label htmlFor="lastName">Фамилия:</label>
          <input
            id="lastName"
            type="text"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            placeholder="Введите фамилию"
          />
          {errors.last_name &&
            errors.last_name.map((msg, i) => (
              <div key={i} className={styles.error}>
                {msg}
              </div>
            ))}
        </div>

        <button
          type="submit"
          className={styles.submitBtn}
          disabled={loading}
        >
          {loading ? "Отправка..." : "Отправить"}
        </button>
      </form>

      {loading && <Spinner />}

      {!loading && dataList.length > 0 && (
        <div className={styles.results}>
          <h2>Результаты:</h2>
          <DataList items={dataList} />
        </div>
      )}
    </div>
  );
};

export default SubmitPage;

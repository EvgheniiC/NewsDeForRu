import { ChangeEvent, useState } from "react";

interface PasswordFieldProps {
  autoComplete?: string;
  id: string;
  label: string;
  maxLength?: number;
  minLength?: number;
  name: string;
  onChange: (value: string) => void;
  required?: boolean;
  value: string;
}

export function PasswordField({
  autoComplete,
  id,
  label,
  maxLength = 256,
  minLength,
  name,
  onChange,
  required = false,
  value,
}: PasswordFieldProps): JSX.Element {
  const [visible, setVisible] = useState<boolean>(false);

  const handleChange = (evt: ChangeEvent<HTMLInputElement>): void => {
    onChange(evt.target.value);
  };

  const toggleVisibility = (): void => {
    setVisible((current) => !current);
  };

  return (
    <>
      <label className="field-label" htmlFor={id}>
        {label}
      </label>
      <div className="password-field-wrap">
        <input
          aria-label={label}
          autoComplete={autoComplete}
          className="operator-login-field password-field-input"
          id={id}
          maxLength={maxLength}
          minLength={minLength}
          name={name}
          onChange={handleChange}
          required={required}
          type={visible ? "text" : "password"}
          value={value}
        />
        <button
          aria-label={visible ? "Скрыть пароль" : "Показать пароль"}
          aria-pressed={visible}
          className="password-field-toggle"
          onClick={toggleVisibility}
          title={visible ? "Скрыть пароль" : "Показать пароль"}
          type="button"
        >
          <span aria-hidden="true">{visible ? "🐵" : "🙈"}</span>
        </button>
      </div>
    </>
  );
}

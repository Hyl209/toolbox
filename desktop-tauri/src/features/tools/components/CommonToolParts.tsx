import type { ReactNode } from "react";
import { uiText } from "../../../uiText";

type ToolHeadingProps = {
  eyebrow: string;
  title: string;
  description: string;
  statusLabel: string;
  ready?: boolean;
  message?: string;
};

export function ToolHeading({ title, description, ready, message }: ToolHeadingProps) {
  return (
    <>
      <div className="tool-heading">
        <div>
          <h2>{title}</h2>
          <p>{description}</p>
        </div>
      </div>
      {message ? <div className={ready ? "info-box" : "error-box"}>{message}</div> : null}
    </>
  );
}

type MultiPathInputProps = {
  label: string;
  countLabel: string;
  value: string;
  disabled?: boolean;
  placeholder: string;
  onChange: (value: string) => void;
  actions?: ReactNode;
};

export function MultiPathInput({
  label,
  countLabel,
  value,
  disabled,
  placeholder,
  onChange,
  actions,
}: MultiPathInputProps) {
  return (
    <label className="field-block">
      <span>
        {label}
        <small>{countLabel}</small>
      </span>
      <textarea disabled={disabled} onChange={(event) => onChange(event.currentTarget.value)} placeholder={placeholder} value={value} />
      {actions ? <div className="field-button-row">{actions}</div> : null}
    </label>
  );
}

type DirectoryPickerRowProps = {
  label: string;
  value: string;
  disabled?: boolean;
  placeholder?: string;
  onChange: (value: string) => void;
  onPick: () => void;
};

export function DirectoryPickerRow({
  label,
  value,
  disabled,
  placeholder = "E:\\output",
  onChange,
  onPick,
}: DirectoryPickerRowProps) {
  return (
    <label className="field-block file-path-field">
      <span>{label}</span>
      <div className="path-input-row">
        <input disabled={disabled} onChange={(event) => onChange(event.currentTarget.value)} placeholder={placeholder} value={value} />
        <button className="path-pick-button" disabled={disabled} onClick={onPick} type="button">
          {uiText.common.choose}
        </button>
      </div>
    </label>
  );
}

type ActionBarProps = {
  hint: string;
  secondary?: ReactNode;
  primary: ReactNode;
  tertiary?: ReactNode;
};

export function ActionBar({ hint, secondary, primary, tertiary }: ActionBarProps) {
  return (
    <div className="actions-row">
      <div className="action-hint">{hint}</div>
      <div className="button-cluster">
        {secondary}
        {tertiary}
        {primary}
      </div>
    </div>
  );
}

type ResultCardProps = {
  label: string;
  value: string;
  detail: string;
};

export function ResultCards({ cards }: { cards: ResultCardProps[] }) {
  return (
    <div className="editor-grid file-editor-grid">
      {cards.map((card) => (
        <div className="result-card" key={card.label}>
          <span>{card.label}</span>
          <strong>{card.value}</strong>
          <p>{card.detail}</p>
        </div>
      ))}
    </div>
  );
}

type RuntimeLogPanelProps = {
  error?: string;
  logs: string[];
};

export function RuntimeLogPanel({ error, logs }: RuntimeLogPanelProps) {
  return (
    <details className="log-panel" aria-label={uiText.common.runtime} open={Boolean(error)}>
      <summary>
        <span>{uiText.common.runtime}</span>
        <small>{error ? uiText.common.hasErrors : logs.length ? `${logs.length} 条` : uiText.common.empty}</small>
      </summary>
      <div className="log-content" aria-live="polite" aria-atomic="false">
        {error ? <div className="error-box">{error}</div> : null}
        {logs.length ? (
          <ul>
            {logs.map((item, index) => (
              <li key={`${item}-${index}`}>{item}</li>
            ))}
          </ul>
        ) : (
          <p className="muted">{uiText.common.noLogs}</p>
        )}
      </div>
    </details>
  );
}

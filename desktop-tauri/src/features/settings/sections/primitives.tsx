import type { ReactNode } from "react";
import { pickDirectory, pickFile, type DialogFilter } from "../../../api/tauri";

type BaseFieldProps = {
  label: ReactNode;
  description?: ReactNode;
  meta?: ReactNode;
  disabled?: boolean;
};

function FieldHead({ label, description, meta }: Omit<BaseFieldProps, "disabled">) {
  return (
    <span className="setting-field-head">
      <b className="field-label">{label}</b>
      {description ? <small className="field-helper">{description}</small> : null}
      {meta ? <small className="field-meta">{meta}</small> : null}
    </span>
  );
}

type SettingTextFieldProps = BaseFieldProps & {
  value: string;
  placeholder?: string;
  onChange: (value: string) => void;
};

export function SettingTextField({
  label,
  description,
  meta,
  value,
  disabled,
  placeholder,
  onChange,
}: SettingTextFieldProps) {
  return (
    <label className="field-block settings-field-card">
      <FieldHead description={description} label={label} meta={meta} />
      <input
        disabled={disabled}
        onChange={(event) => onChange(event.currentTarget.value)}
        placeholder={placeholder}
        type="text"
        value={value}
      />
    </label>
  );
}

type SettingDirectoryFieldProps = BaseFieldProps & {
  value: string;
  placeholder?: string;
  buttonLabel?: string;
  dialogTitle?: string;
  onChange: (value: string) => void;
};

export function SettingDirectoryField({
  label,
  description,
  meta,
  value,
  disabled,
  placeholder,
  buttonLabel = "浏览",
  dialogTitle,
  onChange,
}: SettingDirectoryFieldProps) {
  async function handleBrowse() {
    if (disabled) {
      return;
    }
    const path = await pickDirectory({
      defaultPath: value || undefined,
      title: dialogTitle ?? (typeof label === "string" ? `选择${label}` : "选择目录"),
    });
    if (path) {
      onChange(path);
    }
  }

  return (
    <label className="field-block settings-field-card">
      <FieldHead description={description} label={label} meta={meta} />
      <div className="path-input-row">
        <input
          disabled={disabled}
          onChange={(event) => onChange(event.currentTarget.value)}
          placeholder={placeholder}
          type="text"
          value={value}
        />
        <button className="path-pick-button" disabled={disabled} onClick={handleBrowse} type="button">
          {buttonLabel}
        </button>
      </div>
    </label>
  );
}

type SettingFileFieldProps = BaseFieldProps & {
  value: string;
  placeholder?: string;
  buttonLabel?: string;
  clearLabel?: string;
  dialogTitle?: string;
  filters?: DialogFilter[];
  onChange: (value: string) => void;
  onClear?: () => void;
};

export function SettingFileField({
  label,
  description,
  meta,
  value,
  disabled,
  placeholder,
  buttonLabel = "选择文件",
  clearLabel = "清除",
  dialogTitle,
  filters,
  onChange,
  onClear,
}: SettingFileFieldProps) {
  async function handleBrowse() {
    if (disabled) {
      return;
    }
    const path = await pickFile({
      defaultPath: value || undefined,
      filters,
      title: dialogTitle ?? (typeof label === "string" ? `选择${label}` : "选择文件"),
    });
    if (path) {
      onChange(path);
    }
  }

  return (
    <label className="field-block settings-field-card">
      <FieldHead description={description} label={label} meta={meta} />
      <div className="path-input-row">
        <input
          disabled={disabled}
          onChange={(event) => onChange(event.currentTarget.value)}
          placeholder={placeholder}
          type="text"
          value={value}
        />
        <button className="path-pick-button" disabled={disabled} onClick={handleBrowse} type="button">
          {buttonLabel}
        </button>
        {onClear ? (
          <button className="path-pick-button" disabled={disabled || !value} onClick={onClear} type="button">
            {clearLabel}
          </button>
        ) : null}
      </div>
    </label>
  );
}

type SettingTextareaFieldProps = BaseFieldProps & {
  value: string;
  onChange: (value: string) => void;
};

export function SettingTextareaField({
  label,
  description,
  meta,
  value,
  disabled,
  onChange,
}: SettingTextareaFieldProps) {
  return (
    <label className="field-block settings-field-card">
      <FieldHead description={description} label={label} meta={meta} />
      <textarea disabled={disabled} onChange={(event) => onChange(event.currentTarget.value)} value={value} />
    </label>
  );
}

type SelectOption = {
  label: ReactNode;
  value: string;
};

type SettingSelectFieldProps = BaseFieldProps & {
  value: string;
  options: SelectOption[];
  onChange: (value: string) => void;
};

export function SettingSelectField({
  label,
  description,
  meta,
  value,
  disabled,
  options,
  onChange,
}: SettingSelectFieldProps) {
  return (
    <label className="field-block settings-field-card">
      <FieldHead description={description} label={label} meta={meta} />
      <select disabled={disabled} onChange={(event) => onChange(event.currentTarget.value)} value={value}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

type SettingToggleRowProps = BaseFieldProps & {
  checked: boolean;
  onChange: (checked: boolean) => void;
};

export function SettingToggleRow({
  label,
  description,
  meta,
  checked,
  disabled,
  onChange,
}: SettingToggleRowProps) {
  return (
    <label className="settings-toggle-row">
      <input checked={checked} disabled={disabled} onChange={(event) => onChange(event.currentTarget.checked)} type="checkbox" />
      <FieldHead description={description} label={label} meta={meta} />
    </label>
  );
}

type SettingOutputDirRowProps = {
  label: ReactNode;
  pathKey: string;
  value: string;
  disabled?: boolean;
  description?: ReactNode;
  placeholder?: string;
  onChange: (value: string) => void;
};

export function SettingOutputDirRow({
  label,
  pathKey,
  value,
  disabled,
  description,
  placeholder = "E:\\output",
  onChange,
}: SettingOutputDirRowProps) {
  return (
    <SettingDirectoryField
      buttonLabel="浏览"
      description={description}
      dialogTitle={typeof label === "string" ? `选择${label}` : "选择输出目录"}
      disabled={disabled}
      label={label}
      meta={pathKey}
      onChange={onChange}
      placeholder={placeholder}
      value={value}
    />
  );
}

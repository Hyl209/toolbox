import { SettingToggleRow } from "./primitives";

type AccountPreferencesSectionProps = {
  lastUser?: string;
  rememberPassword: boolean;
  autoLogin: boolean;
  onRememberPasswordChange: (checked: boolean) => void;
  onAutoLoginChange: (checked: boolean) => void;
};

export default function AccountPreferencesSection({
  lastUser,
  rememberPassword,
  autoLogin,
  onRememberPasswordChange,
  onAutoLoginChange,
}: AccountPreferencesSectionProps) {
  return (
    <section className="settings-card settings-wide-card">
      <span>账号偏好</span>
      <p>上次用户：{lastUser || "未记录"}</p>
      <div className="settings-toggle-grid">
        <SettingToggleRow
          checked={rememberPassword}
          description="仅回写旧版 auth/remember_password 开关，不直接处理真实密码内容。"
          label="记住密码偏好"
          meta="auth/remember_password"
          onChange={onRememberPasswordChange}
        />
        <SettingToggleRow
          checked={autoLogin}
          description="关闭记住密码时会自动同步关闭自动登录。"
          label="自动登录"
          meta="auth/auto_login"
          onChange={onAutoLoginChange}
        />
      </div>
    </section>
  );
}

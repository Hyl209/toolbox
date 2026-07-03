type UserMenuProps = {
  lastUser: string;
  open: boolean;
  onClose: () => void;
  onLogout: () => void;
};

function avatarText(lastUser: string): string {
  const clean = lastUser.trim();
  return clean ? clean.slice(0, 1).toUpperCase() : "?";
}

export default function UserMenu({ lastUser, open, onClose, onLogout }: UserMenuProps) {
  if (!open) {
    return null;
  }

  const user = lastUser.trim();
  return (
    <div className="floating-popover user-menu-popover" role="dialog" aria-label="用户菜单">
      <button className="popover-close" onClick={onClose} type="button">
        关闭
      </button>
      <div className="user-menu-avatar">{avatarText(user)}</div>
      <strong>{user || "未登录"}</strong>
      <span>{user ? "已登录" : "未登录"}</span>
      <button className="ghost-button" onClick={onLogout} type="button">
        退出账号
      </button>
    </div>
  );
}

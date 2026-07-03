type SupportPopupProps = {
  open: boolean;
  supportImage: string;
  onClose: () => void;
};

export default function SupportPopup({ open, supportImage, onClose }: SupportPopupProps) {
  if (!open) {
    return null;
  }

  return (
    <div className="modal-scrim" role="presentation" onClick={onClose}>
      <div className="support-popup" role="dialog" aria-label="赞赏" onClick={(event) => event.stopPropagation()}>
        <button className="popover-close" onClick={onClose} type="button">
          关闭
        </button>
        <strong>感谢打赏</strong>
        {supportImage ? <img alt="赞赏二维码" src={supportImage} /> : <p>赞赏图片缺失</p>}
      </div>
    </div>
  );
}

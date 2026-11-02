import { useEffect, useId, useRef } from "react";
import Icon from "./Icon.jsx";

export default function Modal({
  open,
  title,
  onClose,
  children,
  className = "",
}) {
  const ref = useRef(null);
  const titleId = useId();
  useEffect(() => {
    const dialog = ref.current;
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    dialog.showModal();
    document.body.style.overflow = "hidden";
    return () => {
      dialog.close();
      document.body.style.overflow = previousOverflow;
    };
  }, [open]);
  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      className={className}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClick={(event) => {
        if (event.target !== event.currentTarget) return;
        const rect = event.currentTarget.getBoundingClientRect();
        if (
          event.clientX < rect.left ||
          event.clientX > rect.right ||
          event.clientY < rect.top ||
          event.clientY > rect.bottom
        )
          onClose();
      }}
    >
      <h2 id={titleId} className="sr-only">
        {title}
      </h2>
      <button
        className="close-dialog"
        type="button"
        onClick={onClose}
        aria-label={`${title} 닫기`}
      >
        <Icon name="close" />
      </button>
      {open ? children : null}
    </dialog>
  );
}

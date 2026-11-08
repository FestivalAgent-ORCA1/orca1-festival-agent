import { useEffect, useState } from "react";
import Modal from "../common/Modal.jsx";
import Button from "../common/Button.jsx";

const TITLE_MAX = 50;

export default function SaveScheduleDialog({ open, defaultTitle = "", onClose, onSave }) {
  const [title, setTitle] = useState(defaultTitle);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    if (open) {
      setTitle(defaultTitle);
      setError("");
      setSaving(false);
    }
  }, [open, defaultTitle]);

  const submit = async (event) => {
    event.preventDefault();
    const value = title.trim();
    if (!value) return setError("일정 이름을 적어 주세요.");
    setSaving(true);
    setError("");
    try {
      await onSave(value);
    } catch (failure) {
      setError(failure?.message || "일정을 저장하지 못했어요.");
      setSaving(false);
    }
  };

  return (
    <Modal open={open} title="일정 저장" onClose={saving ? () => {} : onClose} className="planner-dialog">
      <form className="planner-form" onSubmit={submit}>
        <span className="eyebrow">SAVE MY DAY</span>
        <h2 className="planner-title">이 하루를 저장할까요?</h2>
        <label className="field">
          <span>일정 이름</span>
          <input
            value={title}
            maxLength={TITLE_MAX}
            onChange={(event) => setTitle(event.target.value)}
            autoFocus
            required
          />
        </label>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <div className="planner-form-actions">
          <Button variant="white" onClick={onClose} disabled={saving}>
            취소
          </Button>
          <Button type="submit" variant="blue" disabled={saving}>
            {saving ? "저장하는 중…" : "저장하기"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

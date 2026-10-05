export default function Input({
  label,
  type = "text",
  placeholder,
  value,
  onChange,
  onKeyDown,
  mono = false,
}) {
  return (
    <div className="fg3">
      {label && <label>{label}</label>}
      <input
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        onKeyDown={onKeyDown}
        style={mono ? { fontFamily: "'DM Mono', monospace" } : {}}
      />
    </div>
  );
}
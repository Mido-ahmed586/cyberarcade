// Variants: "accent" | "ghost" | "plain"
// Sizes: "sm" | "md" | "lg" | "full"

export default function Button({
  children,
  variant = "accent",
  size = "md",
  disabled = false,
  onClick,
  style,
  className = "",
}) {
  const variantClass = {
    accent: "ba2",
    ghost: "bg",
    plain: "bp",
  }[variant];

  const sizeClass = {
    sm: "bs",
    md: "",
    lg: "bl",
    full: "bf",
  }[size];

  return (
    <button
      className={`btn ${variantClass} ${sizeClass} ${className}`}
      onClick={onClick}
      disabled={disabled}
      style={style}
    >
      {children}
    </button>
  );
}

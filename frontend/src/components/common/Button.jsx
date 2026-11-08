export default function Button({
  as: Component = "button",
  variant = "",
  className = "",
  children,
  ...props
}) {
  return (
    <Component
      {...(Component === "button" ? { type: "button" } : {})}
      className={`key ${variant} ${className}`}
      {...props}
    >
      {children}
    </Component>
  );
}

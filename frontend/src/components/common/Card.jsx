export default function Card({
  as: Component = "article",
  className = "",
  children,
  ...props
}) {
  return (
    <Component className={`card ${className}`} {...props}>
      {children}
    </Component>
  );
}

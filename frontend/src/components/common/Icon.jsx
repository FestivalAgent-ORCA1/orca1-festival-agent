const paths = {
  heart: (
    <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z" />
  ),
  arrow: <path d="M4 12h15m-6-6 6 6-6 6" />,
  search: (
    <>
      <circle cx="10.7" cy="10.7" r="6.6" />
      <path d="m16 16 5 5" />
    </>
  ),
  pin: (
    <>
      <path d="M20 10c0 6-8 11-8 11S4 16 4 10a8 8 0 1 1 16 0Z" />
      <circle cx="12" cy="10" r="2.6" />
    </>
  ),
  moon: <path d="M20.9 13.4A9 9 0 0 1 10.6 3.1a9 9 0 1 0 10.3 10.3Z" />,
  apple: (
    <path d="M12 7c-3-3-9-1-9 5 0 5 4 9 6 9 1 0 2-1 3-1s2 1 3 1c2 0 6-4 6-9 0-6-6-8-9-5Zm0 0c0-3 1-5 4-5" />
  ),
  ticket: (
    <>
      <path d="M3 7a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v3a2 2 0 0 0 0 4v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-3a2 2 0 0 0 0-4Z" />
      <path d="M15 5v2m0 3v1m0 3v1m0 2v2" />
    </>
  ),
  close: <path d="m6 6 12 12M6 18 18 6" />,
  spark: (
    <path d="M12 1v7m0 8v7M1 12h7m8 0h7M4.2 4.2 9 9m6 6 4.8 4.8M4.2 19.8 9 15m6-6 4.8-4.8" />
  ),
  chevron: <path d="m8 10 4 4 4-4" />,
  home: <path d="M3 11 12 3l9 8m-16-1.5V21h5v-6h4v6h5V9.5" />,
  chat: (
    <path d="M21 12a8 8 0 0 1-11.6 7.1L4 20.5l1.4-4.6A8 8 0 1 1 21 12Z" />
  ),
  community: (
    <>
      <circle cx="9" cy="8" r="3.4" />
      <path d="M2.5 20c.6-3.7 3.2-6 6.5-6s5.9 2.3 6.5 6" />
      <path d="M15.5 4.9a3.4 3.4 0 0 1 0 6.3M18 14.4c2 .9 3.2 2.9 3.5 5.6" />
    </>
  ),
  user: (
    <>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21c.7-4.2 3.8-7 8-7s7.3 2.8 8 7" />
    </>
  ),
};
export default function Icon({ name, className = "", ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      className={`icon ${className}`}
      aria-hidden="true"
      {...props}
    >
      {paths[name] || paths.ticket}
    </svg>
  );
}

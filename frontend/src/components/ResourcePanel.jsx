export default function ResourcePanel({ title, icon, actions, children }) {
  return (
    <section className="resource-panel">
      <div className="panel-heading">
        <h2>
          {icon}
          {title}
        </h2>
        {actions}
      </div>
      {children}
    </section>
  );
}

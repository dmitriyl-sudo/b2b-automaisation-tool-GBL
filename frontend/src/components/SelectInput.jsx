export default function SelectInput({ name, label, value, onChange, options }) {
    return (
      <div>
        <label className="block text-sm font-medium">{label}</label>
        <input
          list={`datalist-${name}`}
          name={name}
          value={value}
          onChange={onChange}
          className="border w-full p-2"
          placeholder={`Type or select ${label}`}
        />
        <datalist id={`datalist-${name}`}>
          {options.map(opt => (
            <option key={opt} value={opt} />
          ))}
        </datalist>
      </div>
    );
  }
  
interface CompactSelectOption<T extends string> {
  key: T;
  label: string;
}

interface CompactSelectProps<T extends string> {
  ariaLabel: string;
  value: T;
  options: readonly CompactSelectOption<T>[];
  onChange: (value: T) => void;
}

export function CompactSelect<T extends string>({
  ariaLabel,
  value,
  options,
  onChange
}: CompactSelectProps<T>): JSX.Element {
  return (
    <label className="feed-compact-select">
      <select
        aria-label={ariaLabel}
        className="feed-compact-select-control"
        onChange={(event: React.ChangeEvent<HTMLSelectElement>) => {
          onChange(event.target.value as T);
        }}
        value={value}
      >
        {options.map((option: CompactSelectOption<T>) => (
          <option key={option.key} value={option.key}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

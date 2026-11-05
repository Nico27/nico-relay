import type { AccountSummary } from '../types';

interface AccountPickerProps {
  accounts: AccountSummary[];
  selectedId: number | null;
  onChange: (id: number) => void;
}

export function AccountPicker({ accounts, selectedId, onChange }: AccountPickerProps) {
  return (
    <div className="picker">
      <label className="picker__label" htmlFor="account">
        Account
      </label>
      <select
        id="account"
        className="picker__select"
        value={selectedId ?? ''}
        onChange={(event) => onChange(Number(event.target.value))}
      >
        {accounts.map((account) => (
          <option key={account.id} value={account.id}>
            {account.name} — {account.industry}
          </option>
        ))}
      </select>
    </div>
  );
}

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export interface FilterField {
  name: string;
  label: string;
  type?: "text" | "number" | "date";
  placeholder?: string;
}

export function FilterBar({
  fields,
  values,
  onChange,
}: {
  fields: FilterField[];
  values: Record<string, string>;
  onChange: (name: string, value: string) => void;
}) {
  if (fields.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-3">
      {fields.map((field) => (
        <div key={field.name} className="space-y-1">
          <Label htmlFor={field.name} className="text-xs text-muted-foreground">
            {field.label}
          </Label>
          <Input
            id={field.name}
            type={field.type ?? "text"}
            placeholder={field.placeholder}
            value={values[field.name] ?? ""}
            onChange={(e) => onChange(field.name, e.target.value)}
            className="h-8 w-40"
          />
        </div>
      ))}
    </div>
  );
}

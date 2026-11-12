import type { ArtifactCode, ArtifactType } from "../types/artifact-studio.types";

interface ArtifactTypePickerProps {
  types: ArtifactType[];
  selected: ArtifactCode;
  onSelect: (code: ArtifactCode) => void;
}

/** Step 1: radio cards for each artifact type. */
export function ArtifactTypePicker({ types, selected, onSelect }: ArtifactTypePickerProps) {
  return (
    <fieldset className="m-0 border-0 p-0">
      <legend className="mb-(--space-3) p-0 text-(length:--font-size-title-small) leading-(--line-height-title-small) font-semibold">
        1. Select artifact type
      </legend>

      <div className="grid grid-cols-1 gap-(--space-3) sm:grid-cols-2 lg:grid-cols-4">
        {types.map((type) => {
          const isSelected = type.code === selected;
          return (
            <label
              key={type.code}
              className={`flex cursor-pointer items-start gap-(--space-3) rounded-(--radius-lg) p-(--space-4) ${
                isSelected
                  ? "border-2 border-(--color-border-brand-primary) bg-(--color-bg-brand-subtle)"
                  : "border border-(--color-border-default-disabled) bg-(--color-bg-default-primary) hover:border-(--color-border-brand-subtle)"
              }`}
            >
              <input
                type="radio"
                name="artifact-type"
                value={type.code}
                checked={isSelected}
                onChange={() => onSelect(type.code)}
                className="mt-(--space-1) accent-(--color-primary-default)"
              />
              <span>
                <span className="block text-(length:--font-size-body-medium) leading-(--line-height-body-medium) font-semibold">
                  {type.name}
                </span>
                <span className="block text-(length:--font-size-caption) leading-(--line-height-caption) text-(--color-text-default-subtle)">
                  {type.description}
                </span>
              </span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
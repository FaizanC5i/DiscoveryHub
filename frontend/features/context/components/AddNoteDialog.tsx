"use client";

import { Modal } from "@/components/ui/Modal";
import type { NoteInput } from "../types/note";
import { NoteForm } from "./NoteForm";

interface AddNoteDialogProps {
  open: boolean;
  onClose: () => void;
  onSave: (input: NoteInput) => Promise<void>;
}

const EMPTY_NOTE: NoteInput = { title: "", body: "" };

export function AddNoteDialog({ open, onClose, onSave }: AddNoteDialogProps) {
  return (
    <Modal open={open} onClose={onClose} title="Add a note">
      {/* Mounts fresh each time the dialog opens, so no text is left over from the last note. */}
      <NoteForm
        initialValues={EMPTY_NOTE}
        submitLabel="Save note"
        onSubmit={async (input) => {
          await onSave(input);
          onClose();
        }}
        onCancel={onClose}
      />
    </Modal>
  );
}

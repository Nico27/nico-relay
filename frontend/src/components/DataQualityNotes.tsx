import type { Note } from '../types';

interface DataQualityNotesProps {
  notes: Note[];
}

export function DataQualityNotes({ notes }: DataQualityNotesProps) {
  if (notes.length === 0) return null;

  return (
    <section className="panel panel--notes" aria-labelledby="notes-title">
      <header className="panel__head">
        <h2 id="notes-title">About this data</h2>
      </header>
      <ul className="notes">
        {notes.map((note) => (
          <li key={note.code} className={`notes__item notes__item--${note.severity}`}>
            <span className="notes__marker" aria-hidden="true">
              {note.severity === 'warning' ? '!' : 'i'}
            </span>
            <span>
              <span className="visually-hidden">{note.severity}: </span>
              {note.message}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}

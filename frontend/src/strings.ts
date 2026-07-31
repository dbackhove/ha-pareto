// Custom cards cannot reach Home Assistant's translation files, so the few
// strings this one needs are carried here. English and German, matching the
// integration's own translations.

const EN = {
  top: "Most used",
  recent: "Recently used",
  edit: "Edit list",
  done: "Done",
  hide: "Hide from my list",
  pin: "Pin to the top",
  unpin: "Remove pin",
  restore: "Show again",
  hiddenHeading: "Hidden by me",
  empty: "Nothing recorded yet.",
  allHidden: "Everything is hidden. Use edit mode to bring an entry back.",
  noHelpers: "This Home Assistant frontend provides no card helpers.",
  mode: "List",
  title: "Title (empty: named after the list)",
  show_title: "Show the title",
  columns: "Columns (empty: fits the width)",
};

const DE: typeof EN = {
  top: "Meistgenutzt",
  recent: "Zuletzt benutzt",
  edit: "Liste bearbeiten",
  done: "Fertig",
  hide: "Aus meiner Liste ausblenden",
  pin: "Nach oben anheften",
  unpin: "Anheftung lösen",
  restore: "Wieder anzeigen",
  hiddenHeading: "Von mir ausgeblendet",
  empty: "Noch keine Bedienungen erfasst.",
  allHidden: "Alles ausgeblendet. Im Bearbeiten-Modus lässt sich ein Eintrag zurückholen.",
  noHelpers: "Dieses Home-Assistant-Frontend stellt keine Card-Helpers bereit.",
  mode: "Liste",
  title: "Titel (leer: benannt nach der Liste)",
  show_title: "Titel anzeigen",
  columns: "Spalten (leer: passt sich der Breite an)",
};

export type StringKey = keyof typeof EN;

export function translate(language: string | undefined, key: StringKey): string {
  return language?.toLowerCase().startsWith("de") ? DE[key] : EN[key];
}

/** Copy for the UP-RERA complaint draft. */
export const complaint = {
  title: "UP-RERA complaint draft",
  lead: "A starting point built only from what the records say, with the source for each line.",
  banner: "Draft for you to review and file. Not legal advice.",
  editLabel: "Complaint draft (you can edit it)",
  build: "Draft a UP-RERA complaint",
  copy: "Copy draft",
  copied: "Draft copied",
  copyFailed: "Could not copy; select the text instead",
  print: "Print or save as PDF",
  file: "Open the UP-RERA site to file",
  fileNote: "On the UP-RERA site, choose the complaint option and attach the annexures.",
  to: (state: string, rera: string) =>
    `To,\nThe Hon'ble ${state} Real Estate Regulatory Authority (${rera})`,
  subject: (project: string, reraId: string) => `Subject: Complaint about ${project} (${reraId})`,
  promoterUnknown: "the promoter",
  intro: (promoter: string, reraId: string, date: string) =>
    `I am a homebuyer in the project registered as ${reraId} by ${promoter}. The public UP-RERA records read on ${date} show the following:`,
  factsHeading: "Facts from the public records:",
  noFacts: "The public records read did not show a delay, extension, missed report or order to cite. Add your own facts below.",
  prayer:
    "This complaint is made under Section 31 of the Real Estate (Regulation and Development) Act, 2016. I request the Authority to look into the above and direct the promoter as it finds right under the Act.",
  buyerDetails: "My name, unit number, allotment date and amount paid: [add your details]",
  annexureHeading: "Annexures (public pages and the day each was read):",
  annexure: "Annexure",
  readOn: "read on",
};

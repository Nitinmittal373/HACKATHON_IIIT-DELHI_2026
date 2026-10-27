/** Copy for finding a project without its website: the "More ways" panel, results and guidance. */
export const find = {
  more: {
    summary: "More ways to find it",
    lead: "No RERA number, or the project has no website? Try one of these.",
    tabsLabel: "Ways to find a project",
    tabs: { builder: "Builder", locality: "City / locality", document: "Upload brochure", qr: "Scan QR" },
    builder: {
      label: "Builder or company name",
      placeholder: "For example Lodha Developers",
      cityLabel: "City (optional)",
      cityPlaceholder: "For example Noida",
      submit: "Find their projects",
      help: "Lists the projects this builder has registered, with where each number was seen.",
    },
    locality: {
      nameLabel: "Project name",
      namePlaceholder: "For example Eureka Park",
      localityLabel: "City or locality",
      localityPlaceholder: "For example Sector 150, Noida",
      submit: "Search there",
      help: "Add a city in Uttar Pradesh, such as Noida or Lucknow, to narrow the search.",
    },
    document: {
      choose: "Choose a PDF",
      limit: "A brochure or agreement, PDF, up to 5 MB.",
      reading: "Reading the file…",
      privacy:
        "Your file is read in memory only to find the RERA number. It is never saved, and phone numbers, e-mail, PAN and Aadhaar numbers are removed from what we show back. Photos are never uploaded.",
      tooBig: "This file is larger than 5 MB.",
      notPdf: "Please choose a PDF. For a photo, use Scan QR.",
      failed: "We could not read this file.",
    },
    qr: {
      camera: "Open the camera",
      photo: "Or choose a photo of the QR code",
      stop: "Stop the camera",
      hint: "Hold the QR code of the hoarding or brochure inside the frame.",
      scanning: "Looking for a QR code…",
      privacy:
        "The camera and photos stay on your device. Only the text inside the QR code is sent to find the number.",
      noCamera: "The camera could not be opened. You can choose a photo of the QR code instead.",
      noQr: "No QR code was found in this photo.",
      cameraLabel: "Camera view",
    },
    results: {
      titleDocument: "Found in your document",
      titleQr: "Found in your QR code",
      use: "Use this number",
      confirmed: "UP-RERA shows this number.",
      unconfirmed: "The UP-RERA page could not be read for this number yet.",
      none: "We could not find a UP-RERA registration number there.",
    },
  },
  status: {
    confirmed: "On UP-RERA",
    listings_only: "Seen on builder and listing sites",
    from_document: "Found in your document",
    from_order: "Found in a public order",
  },
  statusHelp: {
    confirmed: "A page on up-rera.in prints this number.",
    listings_only:
      "The builder and listing sites print this number, but no UP-RERA page was read for it. A check will try UP-RERA and say what it could not verify.",
    from_document: "Taken from the file you gave us. No UP-RERA page was read for it yet.",
    from_order: "Taken from a public order that names the project. No UP-RERA page was read for it yet.",
  },
  seenOn: (sites: string) => `Seen on: ${sites}`,
  orderLink: "Read the order",
  orderLead: {
    title: "A public order names the builder",
    body: (builder: string) =>
      `We did not find the project on UP-RERA, but a public order about it names ${builder}.`,
    link: "Read the order",
    button: "See this builder's registered projects",
  },
  builderResults: {
    title: (builder: string) => `Registered projects found for “${builder}”`,
    lead: "From UP-RERA and the open web. Pick the project on your agreement.",
    companiesTitle: "Company pages with a similar name",
    companiesNote:
      "Different companies of one group are different legal entities. Check which one signed your agreement.",
    cin: "CIN",
    openPage: "Open the page",
    noneTitle: "No registered projects found for this builder",
    noneBody: (builder: string) =>
      `We could not find a project registered by “${builder}” in public pages. The search reads what is public and can miss projects.`,
    inCity: (city: string) => `Looked in: ${city}`,
  },
  outsideUp:
    "NeevCheck covers Uttar Pradesh RERA projects for now. Check this project on its own state's RERA website.",
  notFound: {
    title: "We couldn't find a RERA registration for this project in public records.",
    note: "This does not mean it has none. Public search can miss a project, and a portal can be down. Nothing was checked and nothing was charged.",
    stepsTitle: "What you can do",
    steps: [
      "Ask the builder for the RERA registration number in writing.",
      "A project of more than 500 square metres of land or more than eight apartments must be registered before it is advertised or sold (RERA Act, Section 3).",
      "Do not pay anything until you can verify the number on UP-RERA.",
    ],
    reportTitle: "If the builder cannot give a number",
    reportLink: "Tell UP-RERA about this project",
    tryTitle: "Other ways to look",
    tryItems: [
      "Search by the builder's name, or add the city or locality.",
      "Upload the brochure or agreement as a PDF, or scan the QR code on the hoarding.",
    ],
    tryButton: "More ways to find it",
  },
};

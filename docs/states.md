# State RERA portals: what NeevCheck can read

Researched on 26 October 2026 with TinyFish Search and Fetch only (no paid agent run read a
portal). Every row below comes from a page or a search result read that day, not from memory.
Where a fact could not be confirmed it says so.

## How a portal is read

| Level | Meaning |
|---|---|
| `full` | Fetch reads the project page and a deterministic parser reads every field. Only UP-RERA today. |
| `partial` | Fetch reads the project page, but it has only some of the fields or needs a link that Search finds first. |
| `search_only` | Fetch cannot read the portal (it answers `proxy_error`, `login_required` or a CAPTCHA). NeevCheck reads what Search returns from the portal's own pages and links to the portal. Confidence drops, and the report says "Unable to verify" for what was not read. |

A stealth agent with an India proxy was also tried once on a MahaRERA project result page and
once on a Karnataka certificate page, starting on the deep page, never a homepage. MahaRERA
showed the same number, name, promoter and district that Search returns, and the project detail
page behind it shows a CAPTCHA, which is never solved, so MH stays `search_only`. The Karnataka
page rendered no data. An India-proxy agent was also tried once on a Haryana page and could not reach the
site either (`ERR_TUNNEL_CONNECTION_FAILED`), so a paid agent does not change a `search_only`
state. Nothing is bypassed: no CAPTCHA, login or paywall is ever attempted.

## Table

| State | Authority | Official domain | Registration number (real examples) | Project page | Gate seen | Readable fields (from Search) | Complaint filing | Level |
|---|---|---|---|---|---|---|---|---|
| UP | UP-RERA | up-rera.in | `UPRERAPRJ8334`, `UPRERAPRJ188811/08/2024` | `Frm_View_Project_Details.aspx?id=` and a Projectsummary page | none | all: promoter, dates, extensions, status, complaints | up-rera.in/ComplaintHome | full |
| MH | MahaRERA | maharera.maharashtra.gov.in | `P99000055716`, `P52100031791`, `P51800000937` | `/projects-search-result?certificate_no=P…`; the full view is on maharerait.maharashtra.gov.in | Fetch: `login_required` (maharerait), `proxy_error` (maharera) | id, name, promoter, district, pincode | /complaint-filing-under-registered-project | search_only |
| HR | HRERA Gurugram and Panchkula | haryanarera.gov.in | Panchkula `HRERA-PKL-JJR-867-2026`, `HRERA-PKL-PNP-495-2023`; Gurugram `RC/REP/HARERA/GGM/1061/793/2026/33`, `RC/REP/HARERA/GGM/856` | `/view_project/searchprojectDetail/{n}` | Fetch and an India-proxy agent both fail | status, approval date, promoter, certificate | haryanarera.gov.in, Complaints tab | search_only |
| KA | K-RERA | rera.karnataka.gov.in | `PRM/KA/RERA/1251/309/PR/190517/002554`, `PRM/KA/RERA/1251/310/PR/160124/006548` | project lists `/viewAllProjects`, `/viewDefaultProjects` (promoter, district, applied, approved, proposed completion) | Fetch: `proxy_error` | promoter, district, approved date, proposed completion | rera.karnataka.gov.in, Complaint | search_only |
| DL | Delhi RERA | erera.co.in (the Delhi RERA e-portal; rera.delhi.gov.in could not be read) | `DLRERA2023P0008`, `DLRERA2022P0036` | `/reradelhiindex/PublicView/ProjectInfo`, registration certificate PDFs | Fetch: `proxy_error` | promoter, registration, validity | /reradelhiindex/GenComplaint/RegComplaint | search_only |
| TG | TG-RERA | rerait.telangana.gov.in (search), rera.telangana.gov.in (information, complaints) | no real number read; the portal's format is `P0` plus 10 digits (not verified) | `/SearchList/Search` | CAPTCHA on search (Fetch shows "Enter the text below as you see in the captcha") | none behind the CAPTCHA | rera.telangana.gov.in/complaint/ | search_only |
| GJ | GujRERA | gujrera.gujarat.gov.in | `PR/GJ/SURAT/SURAT CITY/SUDA/RAA00299/290917`, `PR/GJ/AHMEDABAD/AHMEDABAD CITY/AUDA/RAA04710/210119` | registration certificates at `/vdms/download/{token}` | Fetch: `proxy_error` | registration number, promoter, certificate text | gujrera.gujarat.gov.in (Form A) | search_only |
| TN | TNRERA | rera.tn.gov.in | `TN/01/Layout/0001/2017`, `TNRERA/7/LO/3733/2026` | `/public-view1/building/pfirm/{uuid}` and `/public-view2/…` | Fetch: `proxy_error` | status, completion date, address | rera.tn.gov.in/complaint/login | search_only |
| RJ | RAJ-RERA | rera.rajasthan.gov.in | `RAJ/P/2020/1380`, `RAJ/P/2024/3129` | `/ViewProject?id={token}&type=U` | Fetch: `empty_content` (JavaScript) | project, district, registration date | rera.rajasthan.gov.in | search_only |
| MP | MPRERA | rera.mp.gov.in (listed by MoHUA) | none read from the portal; third-party sites show `P-IND-19-1234` (not verified) | not found by Search | Fetch: `proxy_error` | none | rera.mp.gov.in | search_only |
| WB | WBRERA | rera.wb.gov.in | `WBRERA/P/KOL/2024/002005`, `WBRERA/P/NOR/2024/002226` | `/project_details.php?procode={n}` | Fetch: `proxy_error` | project id, completion and extension date, status, promoter | rera.wb.gov.in, Complaint Registration | search_only |
| PB | RERA Punjab | rera.punjab.gov.in | `PBRERA-SAS79-PR0083` | `/reraindex/publicview/projectinfo` | Fetch: HTTP 522 | registration number, quarterly update | rera.punjab.gov.in | search_only |
| KL | K-RERA | rera.kerala.gov.in | `K-RERA/PRJ/039/2020`, `K-RERA/PRJ/KKD/096/2025` | `/projects?registration_number=…`, `/extension-certificate/{n}` | Fetch: `proxy_error`, HTTP 503 | extensions, validity, promoter | rera.kerala.gov.in | search_only |
| AP | AP RERA | rera.ap.gov.in | `410 OF 2017`, `246 OF 2018` | `/rera/Views/Project.aspx?enc=…` | Fetch: `proxy_error` | registration date, status | rera.ap.gov.in | search_only |
| UK | UKRERA | rera.uk.gov.in (listed by MoHUA) | `UKREP06240000564` (from a certificate PDF) | none found | not read | none | rera.uk.gov.in | search_only |
| BR | RERA Bihar | rera.bihar.gov.in | `BRERAP187328070625271029E00` | `/RegisteredPP.aspx` (list) | none; Fetch reads the list | registration number, promoter, address, date | rera.bihar.gov.in | search_only |
| OD | ORERA | rera.odisha.gov.in | `RP/09/2019/00287`, `RP/07/2024/01240` | `/projects/project-list` | Fetch reads the shell, the data loads with JavaScript | none via Fetch | rera.odisha.gov.in/complaint-status/ | search_only |
| GA | Goa RERA | rera.goa.gov.in | `PRGO08242238`, `PRGO05242234` | `/reraApp/viewProjectDetailPage?projectID={token}` | none | registration number and date, start and end date, status, address | rera.goa.gov.in | partial |
| CG | CG RERA | rera.cgstate.gov.in | `PCGRERA220618000295`, `PCGRERA030424001753` | `/Approved_project_List*.aspx` (lists, including delayed and extended) | Fetch: `proxy_error` | promoter, type, district, approved date, completion | rera.cgstate.gov.in | search_only |
| HP | HP RERA | hprera.nic.in | `RERAHPSOP09170006` | `/PublicDashboard` | none seen; the dashboard needs a form | registration number, promoter | hprera.nic.in | search_only |
| JH | JHARERA | jharera.jharkhand.gov.in | `JHARERA/PROJECT/215/2024`, `JHARERA/PROJECT/132/2021` | `/Home/RegisteredProjectsList` (list) | none; Fetch reads the list | registration number and date, name, developer | jharera.jharkhand.gov.in | search_only |
| AS | RERA Assam | rera.assam.gov.in | `RERAA KM 68 OF 2022-2023`, `RERAA KM 105 OF 2022-2023` | `/view_project/searchprojectDetail/{n}` | Fetch: `proxy_error` | registration number, approval remarks, promoter | rera.assam.gov.in | search_only |
| JK | JK RERA | rera.jk.gov.in | `RERA-JK-JMU-6-2026`, `RERA-JK-JMU-5-2026` | `/view_project/searchprojectDetail/{n}` | Fetch: `proxy_error` | status, hearing date | rera.jk.gov.in | search_only |

## States and territories without a usable public project search

No project number format or project page could be confirmed for these, so they are not in
the registry and a search for them says so instead of guessing: Puducherry (prera.py.gov.in
has project pages, but only promoter numbers such as `PY10714` were seen), Chandigarh
(rera.chd.gov.in, only a PDF was found), Andaman and Nicobar and Ladakh (served from
rera.tn.gov.in and not read), Tripura, Manipur, Meghalaya, Mizoram, Nagaland, Sikkim,
Arunachal Pradesh, Dadra and Nagar Haveli and Daman and Diu, Lakshadweep.

## National fallback

The Unified RERA Portal (rera.mohua.gov.in) is a directory of state authorities, a list of
rules and reports. It has no project search and Fetch cannot read it (`proxy_error`), so it
is only used as the place to find a state's portal address. It adds no coverage.

## What does not depend on the state

The company registry (MCA), insolvency (IBBI and NCLT), news, consumer cases and SARFAESI
notices are national and are read for every state. The Noida, Greater Noida and Yamuna
Expressway land-dues lists exist only for UP; for other states that check is shown as unread
and never counted as a penalty.

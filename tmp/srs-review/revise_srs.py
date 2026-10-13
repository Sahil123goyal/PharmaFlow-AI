from pathlib import Path
import re

src = Path(r'E:\chrome ke downlaods\PharmaFlowAI_SRS (1).tex').read_text(encoding='utf-8-sig')
target = Path(r'G:\Claude_pharma\output\srs\PharmaFlowAI_SRS.tex')
text = src
text = text.replace(r'\newcommand{\Supervisor}{Anushka maam}', r'% Imported supervisor text: Anushka maam. Editable placeholder requested for this revision.'+'\n'+r'\newcommand{\Supervisor}{[Supervisor name and designation]}')
text = text.replace(r'\newcommand{\SubmissionDate}{}', r'\newcommand{\SubmissionDate}{[Submission date]}')
text = text.replace(r'\usepackage{xcolor}', '')
text = text.replace(r'\usepackage{tikz}', r'\usepackage[table]{xcolor}'+'\n'+r'\usepackage{tikz}')
text = text.replace(r'\usetikzlibrary{arrows.meta,positioning,shapes.geometric,fit,calc}', r'\usetikzlibrary{arrows.meta,positioning,shapes.geometric,fit,calc,backgrounds}')
text = text.replace(r'\newcommand{\Proposed}{\textbf{Proposed}}', r'\newcommand{\Proposed}{\textbf{Proposed}}'+'\n'+r'\newcommand{\ToVerify}{\textbf{To verify}}')
styles = r'''\definecolor{uiFill}{HTML}{DAE8FC}
\definecolor{uiStroke}{HTML}{6C8EBF}
\definecolor{logicFill}{HTML}{D5E8D4}
\definecolor{logicStroke}{HTML}{82B366}
\definecolor{dataFill}{HTML}{FFF2CC}
\definecolor{dataStroke}{HTML}{D6B656}
\definecolor{protoFill}{HTML}{FFE6CC}
\definecolor{protoStroke}{HTML}{D79B00}
\definecolor{boundaryFill}{HTML}{F8CECC}
\definecolor{boundaryStroke}{HTML}{B85450}
\definecolor{actorFill}{HTML}{E1D5E7}
\definecolor{actorStroke}{HTML}{9673A6}
\definecolor{noteFill}{HTML}{F5F5F5}
\definecolor{noteStroke}{HTML}{666666}
\tikzset{
  box/.style={draw=uiStroke,fill=uiFill,rounded corners=3pt,line width=1pt,
    align=center,font=\sffamily\small,text width=30mm,minimum height=12mm,inner sep=4pt},
  ui/.style={box},
  process/.style={box,draw=logicStroke,fill=logicFill},
  actor/.style={box,draw=actorStroke,fill=actorFill},
  prototype/.style={box,draw=protoStroke,fill=protoFill},
  boundary/.style={box,draw=boundaryStroke,fill=boundaryFill},
  store/.style={box,draw=dataStroke,fill=dataFill},
  grey/.style={box,draw=noteStroke,fill=noteFill},
  flow/.style={-{Stealth[length=1.6mm,width=1.2mm]},line width=.6pt,draw=noteStroke},
  assoc/.style={line width=.6pt,draw=noteStroke},
  note/.style={font=\sffamily\scriptsize,align=center,fill=white,inner sep=1.5pt},
  decision/.style={diamond,draw=logicStroke,fill=logicFill,line width=1pt,
    aspect=2.1,align=center,font=\sffamily\small,inner sep=3pt},
  dfdstore/.style={rectangle,draw=none,fill=dataFill,align=center,
    font=\sffamily\small,text width=30mm,minimum height=13mm,inner sep=4pt,
    path picture={\draw[dataStroke,line width=1pt]
      (path picture bounding box.north east)--(path picture bounding box.north west)
      --(path picture bounding box.south west)--(path picture bounding box.south east);}},
  activation/.style={draw=logicStroke,fill=logicFill,line width=.6pt},
  life/.style={draw=noteStroke,dashed,line width=.5pt},
  usecase/.style={ellipse,draw=logicStroke,fill=logicFill,line width=1pt,
    font=\sffamily\small,align=center,text width=43mm,minimum height=12mm},
  band/.style={box,text width=150mm,minimum height=23mm},
  classbox/.style={store,align=left,text width=62mm}
}
\newcommand{\SummaryBox}[1]{\par\noindent\colorbox{uiFill}{\parbox{\dimexpr\linewidth-2\fboxsep\relax}{\small\sffamily #1}}\par}
\newcommand{\Criterion}[1]{\multicolumn{4}{@{}p{\textwidth}@{}}{\small\textit{Acceptance / verification:} #1}\\[5pt]}
\newsavebox{\DiagramBox}
'''
text = re.sub(r'\\tikzset\{.*?\n\}', lambda m:styles, text, count=1, flags=re.S)

def figure(body, caption, label):
    return '\\begin{figure}[H]\n\\centering\n'+body.strip()+'\n\\caption{'+caption+'}\\label{'+label+'}\n\\end{figure}'

diagrams = []
diagrams.append(figure(r'''
\begin{tikzpicture}
\node[actor] (user) at (0,0) {Owner/Pharmacist};
\node[process] (auth) at (5,0) {Authenticate and establish session};
\node[ui] (dash) at (10,0) {Dashboard and catalogue counts};
\node[process] (cat) at (10,-3) {Create, inspect, edit and change status};
\node[ui] (report) at (5,-3) {Catalogue report, CSV and print};
\node[process] (voice) at (0,-3) {Bilingual voice / text assistant};
\node[prototype,text width=47mm] (demo) at (10,-6) {Session prototypes: inventory, billing, suppliers, customers; sample analytics};
\node[store,text width=47mm] (db) at (2,-6) {Shared Medicine catalogue; no stock, price or expiry fields};
\draw[flow] (user)--node[note,above]{credentials}(auth);
\draw[flow] (auth)--node[note,above]{login result}(dash);
\draw[flow] (dash)--node[note,right]{medicine forms}(cat);
\draw[flow] (cat)--node[note,above]{report request}(report);
\draw[flow] (voice)--node[note,above]{report intent / link}(report);
\draw[flow] (user)--node[note,left]{reviewed question}(voice);
\draw[flow] (voice.south) |- node[note,pos=.7,above]{active lookup}(db.west);
\draw[flow] (report.south) |- node[note,pos=.7,above]{all-record summary}(db.east);
\draw[flow] (cat.east)--++(.9,0) |- node[note,pos=.7,above]{sample operations}(demo.east);
\end{tikzpicture}''', 'Current workflow. Authenticated catalogue functions use persistent medicine data; operational demo records remain session-scoped.', 'fig:workflow'))

diagrams.append(figure(r'''
\begin{tikzpicture}
\node[grey,text width=44mm] (all) at (0,0) {Pharmacy participants};
\node[actor,text width=38mm] (owner) at (-5,-2.5) {Owner/Pharmacist\\One functional actor};
\node[actor,text width=38mm] (supplier) at (0,-2.5) {Supplier\\Prototype participant};
\node[actor,text width=38mm] (customer) at (5,-2.5) {Customer\\Prototype participant};
\node[ui,text width=38mm] (access) at (-5,-5) {Signed-in operations; admin needs staff status and permissions};
\node[prototype,text width=38mm] (contact) at (0,-5) {Session contact records; no supplier portal};
\node[prototype,text width=38mm] (assist) at (5,-5) {Session contact records; assisted queries, no customer login};
\draw[flow] (all.south)--++(0,-.5)-|(owner.north);
\draw[flow] (all)--(supplier);
\draw[flow] (all.south)--++(0,-.5)-|(customer.north);
\draw[flow] (owner)--(access);\draw[flow] (supplier)--(contact);\draw[flow] (customer)--(assist);
\end{tikzpicture}''', 'User classification. Administration is a permission-controlled capability, not a separate pharmacy business actor.', 'fig:users'))

diagrams.append(figure(r'''
\begin{tikzpicture}
\node[process,text width=44mm,minimum height=21mm] (system) at (0,0) {0.0 PharmaFlowAI\\Django web application with browser interface};
\node[actor,text width=32mm] (staff) at (-5.6,0) {Owner/Pharmacist};
\node[boundary,text width=32mm] (speech) at (5.6,0) {Browser speech service};
\node[actor,text width=40mm] (customer) at (0,3.4) {Customer\\Assisted, signed-in use};
\node[actor,text width=40mm] (reader) at (0,-3.4) {Report reader / browser print destination};
\draw[flow] (staff.north)--++(0,.95)-|node[note,pos=.25,above]{credentials, medicine forms,\\supplier/customer details}(system.150);
\draw[flow] (system.210)|-node[note,pos=.75,below]{pages, results, saved-record feedback}([yshift=-9mm]staff.south)--(staff.south);
\draw[flow] (system.30)|-node[note,pos=.75,above]{audio / reply text, language}([yshift=9mm]speech.north)--(speech.north);
\draw[flow] (speech.south)--++(0,-.95)-|node[note,pos=.25,below]{transcript / spoken reply}(system.330);
\draw[flow] ([xshift=-9mm]customer.south)--node[note,left]{question,\\language}([xshift=-9mm]system.north);
\draw[flow] ([xshift=9mm]system.north)--node[note,right]{catalogue answer,\\prescription flag / fallback}([xshift=9mm]customer.south);
\draw[flow] (system.south)--node[note,right]{CSV, counts,\\printable catalogue}(reader.north);
\end{tikzpicture}''', 'DFD Level 0. Customers use an authenticated counter session. Supplier details are entered by the Owner/Pharmacist; no supplier portal exists. Audio is processed through browser speech services, not uploaded to Django.', 'fig:dfd0'))

diagrams.append(figure(r'''
\begin{tikzpicture}
\foreach \y/\id/\name in {0/1/Authenticate and manage session,-3.2/2/Maintain and query catalogue,-6.4/3/Summarize and export catalogue,-9.6/4/Classify text and build reply,-12.8/5/Edit prototype records}{
  \node[process,text width=31mm,minimum height=16mm] (p\id) at (0,\y) {\id.0\\\name};}
\node[actor] (a1) at (-5.3,0) {Owner/Pharmacist};
\node[actor] (a2) at (-5.3,-3.2) {Owner/Pharmacist};
\node[actor] (a3) at (-5.3,-6.4) {Owner/Pharmacist / report reader};
\node[actor] (a4) at (-5.3,-9.6) {Owner/Pharmacist / assisted Customer};
\node[actor] (a5) at (-5.3,-12.8) {Owner/Pharmacist};
\node[dfdstore] (d1) at (5.3,0) {D1: User accounts and Django sessions};
\node[dfdstore] (d2) at (5.3,-3.2) {D2: Medicine records};
\node[dfdstore] (d3) at (5.3,-6.4) {D2: Medicine records (same store)};
\node[dfdstore] (d4) at (5.3,-9.6) {D2: Medicine records (same store)};
\node[dfdstore,fill=protoFill] (d5) at (5.3,-12.8) {D1: Session prototype payload};
\foreach \i/\request/\response/\query/\result in {
1/{credentials, remember me}/{session / login result}/{account lookup, session write}/{account / session data},
2/{search, filters, fields}/{matches, validation result}/{read, create, update status}/{medicine fields, saved state},
3/{report / export request}/{counts, CSV, print view}/{all-record query}/{rows, status, categories},
4/{reviewed text, language}/{reply, report link, fallback}/{active lookup / summary}/{matches, flags, counts},
5/{supplier/customer and demo edits}/{sample rows, demo export}/{read / write payload}/{current-session rows}}{
  \draw[flow] ([yshift=4mm]a\i.east)--node[note,above,text width=27mm]{\request}([yshift=4mm]p\i.west);
  \draw[flow] ([yshift=-4mm]p\i.west)--node[note,below,text width=27mm]{\response}([yshift=-4mm]a\i.east);
  \draw[flow] ([yshift=4mm]p\i.east)--node[note,above,text width=27mm]{\query}([yshift=4mm]d\i.west);
  \draw[flow] ([yshift=-4mm]d\i.west)--node[note,below,text width=27mm]{\result}([yshift=-4mm]p\i.east);}
\end{tikzpicture}''', 'DFD Level 1. Repeated actors and D2 symbols denote the same participant or store. D1 contains framework sessions and the prototype payload, not an operational ledger. Processes 2.0--5.0 require an authenticated session; speech conversion surrounds process 4.0 in the browser.', 'fig:dfd1'))

diagrams.append(figure(r'''
\begin{tikzpicture}
\node[band,minimum height=28mm] (ui) at (0,0) {};
\node[font=\sffamily\small\bfseries,align=left,text width=25mm] at (-5.9,0) {Presentation};
\node[ui,text width=29mm] at (-2.2,0) {Templates, CSS, forms};
\node[ui,text width=29mm] at (1.5,0) {JavaScript, chat panel};
\node[ui,text width=29mm] at (5.2,0) {Browser speech input / output};
\node[band,fill=logicFill,draw=logicStroke,minimum height=36mm] (logic) at (0,-4.1) {};
\node[font=\sffamily\small\bfseries,align=left,text width=25mm] at (-5.9,-4.1) {Application\\Django monolith};
\node[process,text width=29mm] at (-2.2,-4.1) {Accounts\\Authentication};
\node[process,text width=29mm] at (1.5,-4.1) {Medicines\\Views / forms};
\node[process,text width=29mm] at (5.2,-4.1) {Core\\Dashboard, chat, reports};
\node[band,fill=dataFill,draw=dataStroke,minimum height=31mm] (data) at (0,-8.3) {};
\node[font=\sffamily\small\bfseries,align=left,text width=25mm] at (-5.9,-8.3) {Data\\ORM / sessions};
\node[store,text width=29mm] at (-2.2,-8.3) {User and Medicine};
\node[prototype,text width=29mm] at (1.5,-8.3) {Django Session\\Demo payload};
\node[store,text width=29mm] at (5.2,-8.3) {SQLite default / PostgreSQL configured};
\draw[flow] ([xshift=-8mm]ui.south)--node[note,left]{HTTP forms / JSON\\Routing, authentication, CSRF}([xshift=-8mm]logic.north);
\draw[flow] ([xshift=8mm]logic.north)--node[note,right]{HTML / JSON responses}([xshift=8mm]ui.south);
\draw[flow] ([xshift=-8mm]logic.south)--node[note,left]{ORM queries / session writes}([xshift=-8mm]data.north);
\draw[flow] ([xshift=8mm]data.north)--node[note,right]{records / session state}([xshift=8mm]logic.south);
\end{tikzpicture}''', 'Layered component architecture. All application modules share the Django monolith. WSGI/ASGI hooks and PostgreSQL configuration do not establish production deployment.', 'fig:architecture'))

diagrams.append(figure(r'''
\begin{tikzpicture}
\node[ui,text width=38mm] (open) at (0,0) {Open add/edit form};
\node[ui,text width=38mm] (submit) at (0,-2.1) {Enter medicine fields and submit POST};
\node[process,text width=38mm] (norm) at (0,-4.2) {Normalize whitespace; validate required name};
\node[decision,text width=28mm] (valid) at (0,-6.6) {Valid and not duplicate?};
\node[boundary,text width=35mm] (error) at (-5.2,-6.6) {Show field errors; retain bound form};
\node[store,text width=38mm] (save) at (0,-9) {Save through ORM; enforce unique combination};
\node[ui,text width=38mm] (detail) at (0,-11.2) {Redirect to details; show success};
\draw[flow] (open)--(submit);\draw[flow] (submit)--(norm);\draw[flow] (norm)--(valid);
\draw[flow] (valid)--node[note,above]{No}(error);
\draw[flow] (error.north)|-node[note,pos=.25,left]{correct fields}(submit.west);
\draw[flow] (valid)--node[note,right]{Yes}(save);\draw[flow] (save)--(detail);
\end{tikzpicture}''', 'Catalogue creation/edit activity. Invalid submissions retain the form. Separate POST status actions deactivate or reactivate records; application forms do not delete medicines.', 'fig:activity'))

diagrams.append(figure(r'''
\begin{tikzpicture}
\node[actor,text width=23mm] at (0,0) {User};
\node[ui,text width=23mm] at (4,0) {Browser};
\node[process,text width=23mm] at (8,0) {Django};
\node[store,text width=23mm] at (12,0) {Catalogue};
\foreach \x in {0,4,8,12}{\draw[life] (\x,-.7)--(\x,-9);}
\draw[activation] (3.88,-1) rectangle (4.12,-8.4);
\draw[activation] (7.88,-4.6) rectangle (8.12,-7.1);
\draw[activation] (11.88,-5.5) rectangle (12.12,-6.3);
\draw[flow] (0,-1.1)--node[note,above]{1. Start microphone}(3.88,-1.1);
\node[boundary,text width=48mm,minimum height=10mm,font=\sffamily\scriptsize] at (8,-1.7) {Browser speech service produces a transcript};
\draw[flow] (4.12,-1.7)--(5.45,-1.7);
\draw[flow] (3.88,-2.8)--node[note,above]{2. Display transcript}(0,-2.8);
\draw[flow] (0,-3.7)--node[note,above]{3. Review and Send}(3.88,-3.7);
\draw[flow] (4.12,-4.6)--node[note,above]{4. Text, language, CSRF}(7.88,-4.6);
\draw[flow] (8.12,-5.5)--node[note,above]{5. Validate / query}(11.88,-5.5);
\draw[flow,dashed] (11.88,-6.3)--node[note,above]{6. Matching records}(8.12,-6.3);
\draw[flow,dashed] (7.88,-7.1)--node[note,above]{7. JSON reply}(4.12,-7.1);
\draw[flow] (3.88,-8.2)--node[note,above]{8. Text; optional speech}(0,-8.2);
\node[store,text width=120mm,minimum height=15mm] at (6,-10) {Review before send; no audio upload to Django. Typed input starts at step 3. Medical or unsupported requests may reply without querying the catalogue.};
\end{tikzpicture}''', 'Voice-assistant sequence with activation bars. Recognition and speech synthesis are browser-dependent; Django receives reviewed text and language only.', 'fig:voice-sequence'))

oldfigs = list(re.finditer(r'\\begin\{figure\}\[H\].*?\\end\{figure\}', text, re.S))
assert len(oldfigs)==7
for match, new in reversed(list(zip(oldfigs,diagrams))):
    text=text[:match.start()]+new+text[match.end():]

# All existing requirements remain verbatim; priority and status become explicit columns.
def requirements_table(match):
    block=match.group(0)
    if not re.search(r'^(FR-|NFR-)',block,re.M): return block
    lines=block.splitlines()
    out=[r'\begingroup\small\setlength{\tabcolsep}{4pt}', r'\begin{longtable}{@{}L{25mm}L{88mm}L{16mm}L{22mm}@{}}']
    for line in lines[1:]:
        if line.startswith(r'\toprule'):
            tail=line.split(r'\midrule',1)[1]
            out.append(r'\toprule ID & Requirement & Priority & Status\\\midrule'+tail)
        elif line.startswith(('FR-','NFR-')):
            ident, a, b=line[:-2].split(' & ',2)
            if ident.startswith('FR-'):
                requirement, criterion=a,b
                status='Prototype' if ident.startswith('FR-DEMO') else 'Implemented'
                priority='Medium' if ident.startswith('FR-DEMO') or ident=='FR-AUTH-07' or ident in ['FR-VA-05','FR-VA-06','FR-VA-07','FR-VA-08','FR-VA-09','FR-VA-10'] else 'High'
            else:
                oldstatus,requirement=a,b
                status='To verify' if oldstatus=='Conditional' or ident in ['NFR-PER-03','NFR-PER-04'] else ('Implemented' if oldstatus=='Implemented / conditional' else oldstatus)
                priority='Medium' if ident.startswith(('NFR-PER','NFR-USA','NFR-MAI','NFR-SCA')) else 'High'
                criterion=nfr_checks[ident]
                if oldstatus=='Conditional': criterion='Conditional on the target environment; '+criterion
                if oldstatus=='Implemented / conditional': criterion='Application behaviour is implemented; external-provider behaviour remains conditional. '+criterion
            out.append(f'{ident} & {requirement} & {priority} & {status}'+r'\\*')
            out.append(r'\Criterion{'+criterion+'}')
        elif line==r'\end{longtable}': out.extend([line,r'\endgroup'])
        else: out.append(line)
    return '\n'.join(out)

nfr_checks={
'NFR-PER-01':'With 21 matching records, page 1 shows 20 and page 2 shows one; search/status/category selections remain in page links.',
'NFR-PER-02':'Submit boundary inputs and a dataset with more than 40 candidates; no successful reply exceeds five displayed medicine results. Candidate-count instrumentation remains To verify.',
'NFR-PER-03':'To verify: proposed k6 HTTP benchmark, 10 concurrent authenticated users, 10,000 seeded records, 2-minute warm-up and 10-minute run; measure endpoint-specific p95, target at most 2 seconds. Reference host CPU/RAM/OS, Python/Django versions, database/version and dataset seed must be recorded and agreed before execution. Exclude browser speech.',
'NFR-PER-04':'To verify: proposed k6 benchmark on the same documented host with 10,000 records; run 30 sequential full-report requests and 30 CSV downloads after warm-up, target p95 at most 10 seconds and 100 percent record completeness. Record peak server memory; acceptable memory ceiling and concurrency remain to be agreed.',
'NFR-SEC-01':'All invalid-credential test cases leave the client unauthenticated; normal responses contain neither supplied passwords nor stored password hashes.',
'NFR-SEC-02':'For every protected page in the route inventory, anonymous GET redirects to login. Anonymous chat POST with a valid CSRF context returns 401; authenticated unsafe requests without a valid token return 403. Target: 100 percent of enumerated cases rejected; complete route-matrix execution is To verify.',
'NFR-SEC-03':'Every tested external next URL is rejected; a valid local URL is accepted. Inspect HttpOnly/SameSite settings separately from production HTTPS deployment.',
'NFR-SEC-04':'Before release, document and pass every applicable deployment-checklist item for secret key, hosts, TLS, cookie flags, HSTS and proxy trust; deployment evidence remains To verify.',
'NFR-SEC-05':'Exercise formula-triggering CSV cells, malicious chat text and an external report URL; target zero executable formulas, DOM script insertions or accepted external report links in the agreed fixtures. Full security fixture coverage is To verify.',
'NFR-SEC-06':'Proposed: create an operation-by-permission test matrix; require all allowed cases to succeed and all denied cases to fail before calling the policy enforced.',
'NFR-SEC-07':'Proposed: agree rate limits, audit-event schema, retention and access rules, then test each threshold and logged event. Numeric thresholds are to be agreed.',
'NFR-REL-01':'Create, edit and toggle a record, then read it from another authenticated session; values and identifier remain intact. Confirm that prototype edits do not become shared domain rows.',
'NFR-REL-02':'Simulate denial, expiry and cancellation; input controls recover, retryable drafts remain, and zero late replies are appended after clear/close. Network-path coverage is To verify.',
'NFR-USA-01':'Manually traverse sign-in, catalogue form and assistant with the keyboard; each input has an accessible name and every validation error is perceivable. Full manual accessibility results are To verify.',
'NFR-USA-02':'Test one supported and one unsupported recognition environment plus denied microphone access; English/Hindi text remains usable in all cases. Record browser/device versions and available voices; live results are To verify.',
'NFR-MAI-01':'Inspect responsibilities of accounts, medicines and core, then run both recorded regression commands; acceptance requires zero failing tests. The historical counts remain 85 Django tests and 9 JavaScript tests.',
'NFR-SCA-01':'Proposed: agree concurrent-update workloads and a PostgreSQL migration rehearsal; record conflicts, errors and integrity results before asserting capacity.',
'NFR-REC-01':'Proposed, to be agreed: RPO (maximum permissible data loss) and RTO (maximum restoration time). In a restore drill, measure the recovered backup timestamp, elapsed restore time and row-count/integrity checks against the agreed RPO/RTO; no value or successful drill is established.',
'NFR-PRI-01':'Clear and reload the page and inspect application storage/network behaviour; no application conversation history is restored and Django receives text, not audio. Browser-provider retention remains To verify.'}
text=re.sub(r'\\begin\{longtable\}.*?\\end\{longtable\}',requirements_table,text,flags=re.S)

# Definitions and original source references move into Introduction without losing their entries.
term_match=re.search(r'\\subsection\{Terminology\}\n(.*?)\n\\end\{document\}',text,re.S)
terms=re.findall(r'\\item\[([^]]+)\] (.*)',term_match.group(1))
terms=[('SRS','Software Requirements Specification.'),('CSV','Comma-separated values, used for the catalogue export.'),('DFD',dict(terms)['DFD'])]+[(k,v) for k,v in terms if k!='DFD']+[('RPO / RTO','Recovery point objective / recovery time objective; both remain to be agreed.'),('LLM','Large language model; no external LLM is used by this baseline.'),('API / HTTP','Application programming interface / Hypertext Transfer Protocol.')]
definitions='\\subsection{Definitions, Acronyms and Abbreviations}\\label{sec:terms}\n\\begin{longtable}{@{}L{32mm}L{124mm}@{}}\n\\caption{Definitions and abbreviations}\\\\\n\\toprule Term & Definition\\\\\\midrule\\endfirsthead\n\\toprule Term & Definition\\\\\\midrule\\endhead\n\\bottomrule\\endfoot\n'+'\n'.join(k+' & '+v+r'\\' for k,v in terms)+'\n\\end{longtable}\n'
refs_match=re.search(r'\\subsection\{Source References\}\n(.*?)\n\\subsection\{Terminology\}',text,re.S)
refs=refs_match.group(1)
references=r'''\subsection{References}\label{sec:references}
\begin{description}[style=nextline,leftmargin=12mm]
\item[R01] IEEE Std 830-1998, \emph{IEEE Recommended Practice for Software Requirements Specifications}. Historical structural reference, not a certification claim. \url{https://ieeexplore.ieee.org/document/720574}.
\item[R02] Django Software Foundation, \emph{Django documentation}. Consult documentation matching the recorded project version; this link does not change the baseline. \url{https://docs.djangoproject.com/}.
\item[R03] Python Software Foundation, \emph{Python 3.13 documentation}. \url{https://docs.python.org/3.13/}.
\item[R04] Supplied \emph{SAMS SRS v2.0}, used only for diagram appearance and structural ideas in this revision. None of its domain content is adopted.
\end{description}
'''+refs+'\n'
text=text[:refs_match.start()]+r'''\subsection{Source References}
The complete source list S01--S10 is retained in Section~\ref{sec:references}. S01 records the original structural reference; R04 records the additional visual reference used for this revision.

\subsection{Terminology}
The original terminology is merged into the two-column definitions table in Section~\ref{sec:terms}.
\end{document}
'''
text=text.replace(r'\clearpage'+'\n'+r'\section{Overall Description}',definitions+'\n'+references+'\n'+r'\clearpage'+'\n'+r'\section{Overall Description}',1)
text=text.replace('Sources: S02, S03 and S09 in Section 5.5.','Sources: S02, S03 and S09 in Section~\\ref{sec:references}.')
text=text.replace('data model and source references in Sections 2 and 5.','data model and source references in Sections 2 and 1.5.')
text=text.replace(r'\item \Proposed: a future requirement or measurable target not established as implemented or achieved.',r'\item \Proposed: a future requirement or measurable target not established as implemented or achieved.'+'\n'+r'\item \ToVerify: a target, environment-dependent behaviour or acceptance check for which measured evidence is not established. This does not by itself imply an unimplemented feature.')

# Preserve the revision history, moving it to a dedicated control page.
rev=re.search(r'\\begin\{table\}\[H\]\n\\centering\\small\n\\caption\{Document revision record\}.*?\\end\{table\}',text,re.S).group(0)
text=text.replace(rev,'Document version remains 1.0; see the Document Control page for the original revision record and this editorial revision note.')
control=r'''\section*{Document Control}
\addcontentsline{toc}{section}{Document Control}
\SummaryBox{Catalogue, reports and bilingual assistance; operational modules remain session prototypes.}
\begin{table}[H]\centering\small
\caption{Document control information}\label{tab:control}
\begin{tabularx}{\textwidth}{L{36mm}Y}
\toprule Field & Value\\\midrule
Document & PharmaFlowAI Software Requirements Specification\\
Version / baseline & 1.0 / \BaselineDate\\
Purpose & Academic assessment, maintenance and verifiable scope definition\\
Implementation status & Implemented, Prototype, Proposed and To verify are kept distinct; test results are bounded evidence.\\
Technology baseline & Python 3.13.9, Django 6.1; SQLite default, PostgreSQL configurable; Django templates and JavaScript; browser-dependent speech.\\
Academic details & \Department; \Institution; \Course\\
Pending metadata & \Supervisor; \SubmissionDate\\
\bottomrule\end{tabularx}\end{table}
'''+rev+r'''
\textbf{Editorial revision note (version unchanged).} Diagram styling, explicit requirement priorities/statuses, permissions, traceability and acceptance planning are expanded. No implementation change or new test execution is asserted. The implementation baseline remains 12 October 2026.
\clearpage
'''
text=text.replace(r'\setcounter{page}{2}'+'\n'+r'\tableofcontents',r'\setcounter{page}{2}'+'\n'+control+r'\tableofcontents'+'\n'+r'\clearpage\listoffigures\clearpage\listoftables',1)
text=text.replace('Supervisor and submission date remain placeholders because these details were not supplied.','Supervisor and submission date remain editable placeholders as requested for this revision; the imported supervisor value is retained only in a source comment.')

# Further content and diagrams are appended from authored fragments.
fragments=Path(__file__).with_name('additions.tex').read_text(encoding='utf-8')
parts=dict(re.findall(r'% BEGIN ([A-Z_]+)\n(.*?)% END \1',fragments,re.S))
text=text.replace(r'\subsection{Product Functions}',parts['PERMISSIONS']+'\n'+r'\subsection{Product Functions}',1)
text=text.replace(r'\subsection{Operating Environment}',parts['ER']+'\n'+r'\subsection{Operating Environment}',1)
text=text.replace(r'\subsubsection{External interfaces}',parts['CONSTRAINTS']+'\n'+r'\subsubsection{External interfaces}',1)
text=text.replace(r'\subsubsection{Use cases and detailed scenarios}',parts['USECASE']+'\n'+r'\subsubsection{Use cases and detailed scenarios}',1)
text=text.replace(r'\clearpage'+'\n'+r'\section{System Features}',parts['STATES']+'\n'+r'\clearpage'+'\n'+r'\section{System Features}',1)
text=text.replace(r'\clearpage'+'\n'+r'\section{Other Nonfunctional Requirements}',parts['ACCEPTANCE']+'\n'+r'\clearpage'+'\n'+r'\section{Other Nonfunctional Requirements}',1)
text=text.replace(r'\subsection{Verification and Acceptance Mapping}',parts['PHASES']+'\n'+r'\subsection{Verification and Acceptance Mapping}',1)
text=text.replace(r'\textbf{Baseline verification note.}',parts['TRACE']+'\n'+r'\textbf{Baseline verification note.}',1)
text=text.replace(r'\begin{figure}[H]',parts['LEGEND']+'\n'+r'\begin{figure}[H]',1)
text=text.replace('Its university result-processing entities and technologies are not carried into \\Project.','Neither reference supplies project features or implementation technologies for \\Project.')
start=text.index(r'\subsection{Reference Alignment and Document Control}')
end=text.index(r'\subsection{Source References}',start)
text=text[:start]+r'''\subsection{Reference Alignment and Document Control}
The original five numbered chapters and their existing subsections are retained. Definitions and references are consolidated into Sections 1.4 and 1.5, with pointers preserved in Sections 5.5 and 5.6. New third-level subsections add permissions, constraints, diagrams and acceptance planning without removing existing requirements.

The original S01 reference supplied the chapter hierarchy and academic presentation. The additional R04 reference supplies only visual and structural ideas: pastel diagram palettes, layered architecture, explicit diagram boundaries and document-control information. All actors, data and requirements remain PharmaFlowAI-specific. DFDs represent logical information flows; the class/ER view represents the actual data model. Use-case and state diagrams clarify existing interactions rather than establish new features.

Serif body text, sans-serif numbered headings, A4 pages, contents, lists of figures/tables, numbered captions and page numbers are retained. Page count follows the content rather than a reference document's length. Version remains 1.0 and the implementation baseline remains 12 October 2026. This editorial revision does not claim new test results.

'''+text[end:]
text=text.replace('Transactional inventory / billing & Future & Proposed','Transactional inventory / billing & Medium & Proposed')

future=re.search(r'\\begin\{table\}\[H\]\n\\centering\\small\n\\caption\{Future work, explicitly outside the implemented baseline\}.*?\\end\{table\}',text,re.S)
future_rows=re.findall(r'^(FUT-\d+) & (.*?) & (.*?)\\\\$',future.group(0),re.M)
future_table=r'''\begingroup\small\setlength{\tabcolsep}{4pt}
\begin{longtable}{@{}L{25mm}L{88mm}L{16mm}L{22mm}@{}}
\caption{Future work, explicitly outside the implemented baseline}\\
\toprule ID & Requirement & Priority & Status\\\midrule\endfirsthead
\toprule ID & Requirement & Priority & Status\\\midrule\endhead
\bottomrule\endfoot
'''
for ident,capability,design in future_rows:
    future_table+=f'{ident} & {capability} & Medium & Proposed'+r'\\*'+'\n'+r'\Criterion{Required design before acceptance: '+design+'}\n'
future_table+=r'\end{longtable}\endgroup'
text=text[:future.start()]+future_table+text[future.end():]

# Validate conservation of every original FR/NFR and its prose before writing.
text=text.replace(r'\begin{tikzpicture}',r'\begin{lrbox}{\DiagramBox}\begin{tikzpicture}')
text=text.replace(r'\end{tikzpicture}',r'\end{tikzpicture}\end{lrbox}'+'\n'+r'\ifdim\wd\DiagramBox>\linewidth\resizebox{\linewidth}{!}{\usebox{\DiagramBox}}\else\usebox{\DiagramBox}\fi')
original_ids=re.findall(r'^(?:FR|NFR)-[A-Z]+-\d+',src,re.M)
new_ids=re.findall(r'^(?:FR|NFR)-[A-Z]+-\d+',text,re.M)
assert original_ids==new_ids, (original_ids,new_ids)
for line in src.splitlines():
    if line.startswith(('FR-','NFR-')):
        ident,a,b=line[:-2].split(' & ',2)
        assert (a in text if ident.startswith('FR-') else b in text), ident
        if ident.startswith('FR-'): assert b in text, ident+' criterion'
assert text.count(r'\begin{figure}')==11
assert text.count(r'\begin{figure}')==text.count(r'\end{figure}')
assert '85 Django tests' in text and 'nine JavaScript tests' in text
target.write_text(text,encoding='utf-8')
print(f'Saved {target}: {len(text)} characters; {len(original_ids)} preserved requirements; 11 diagrams.')

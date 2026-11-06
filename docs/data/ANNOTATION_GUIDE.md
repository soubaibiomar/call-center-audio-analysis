# Darija / French code-switching transcription guidance

Apply only to recordings with documented analysis and annotation permission. A
reviewer must separately approve training/evaluation use; possession of an audio
file or an analysis report does not confer that approval. Work in approved private
storage; never put recordings, raw transcripts, identities or sensitive evidence
into Git or UI mock data.

1. Give each conversation and every speaker a stable project-wide pseudonymous ID.
   Maintain the identity key separately with restricted access. Record all speakers,
   including cross-talk; do not invent identities or try to re-identify speakers.
   Respect source-specific prohibitions on identity investigation. Unknown linkage must
   be resolved before making a speaker-disjoint claim.
2. Transcribe what is audible in the original language and original writing system.
   Preserve turns and start/end timestamps. Mark unintelligible speech, overlap and
   uncertain spans with agreed explicit labels; do not infer names or factual details.
3. Mark Darija as ar-MA and French as fr, with language-span boundaries where they
   change. Arabic-script Darija, Latin/Arabizi and French can coexist; retain the
   original script in the reference. Do not silently translate code switches.
4. Before any WER run, version the normalization policy separately: Unicode NFC,
   whitespace/punctuation decisions, case rules and the treatment of Arabic spelling,
   numerals, elongation and Arabizi. Do not mix scripts or apply an undocumented
   transliteration. Preserve raw reviewed reference separately from normalized output.
5. Record whether each label is human verified, unreviewed or machine only. Machine
   pseudo-labels are never gold; human correction requires an independently reviewed
   revision, reviewer pseudonym, provenance and an approved purpose.
6. Use two independently reviewed transcriptions on an agreed audit sample, resolve
   disagreements with a third reviewer, record adjudication and report sample size and
   agreement method. No label agreement is measured until such data exists.
7. Document privacy minimization/redaction, source/subset license, retention deadline,
   review date and provenance reference for every record. Changes to locked test
   material require a new reviewed dataset version and a new explicitly approved lock.

The current manifest stores metadata and label status only, not transcript text.
The policy does not establish that a human review or consent actually occurred;
operators must verify real evidence and control authorization separately.

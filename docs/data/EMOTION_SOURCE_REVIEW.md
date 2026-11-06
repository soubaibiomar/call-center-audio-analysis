# STEP_20 dataset/source review — 2026-10-29

Evaluation purpose only; no training, contact with authors, re-identification or source-audio redistribution. The task authorized public-source discovery and evaluation. Acquisition was a bounded 19,870,333-byte operation, not a full corpus download. Local material is ignored under `.local/step20-corpora`; use the existing project review deadline 2026-11-28, with manual retention review rather than claiming automatic deletion.

| Candidate | Primary evidence | Outcome |
|---|---|---|
| CREMA-D | [Author repository](https://github.com/CheyneyComputerScience/CREMA-D), [license](https://raw.githubusercontent.com/CheyneyComputerScience/CREMA-D/master/LICENSE.txt) | ODbL 1.0 database / DbCL 1.0 contents. Cite Cao et al., CREMA-D, IEEE TAFFC 2014, DOI 10.1109/TAFFC.2014.2336244. Used 16 acted-English audio clips and source audio-majority labels, not filename intended emotion. Preserve attribution/license; no source redistribution. The repository requests a usage-tracking form; no personal details or message were submitted. |
| MDER-MA original | [Version 1 record](https://data.mendeley.com/datasets/yzsw3ff6rn/1), DOI 10.17632/yzsw3ff6rn.1; [source paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12433488/) | Original record explicitly lists CC BY 4.0. Darija media speech with source human annotations; not telephone calls. Cite Ouali and El Garouani (2025). This source grant is not independent verification of every underlying media/privacy right. |
| MDER-MA mirror | [Repository](https://huggingface.co/datasets/FatimahEmadEldin/Moroccan-Arabic-Multimodal-Emotion-Recognition) | Mirror defers license to original; its uncertainty was resolved at the original CC BY record for this limited evaluation. Used 16 adult-age-metadata clips; native-annotator majority provenance is source-published, not independently reviewed by this project. No age or demographic inference beyond the selection filter. |
| MORAD | [Author repository/access conditions](https://github.com/houdaipha/morad) | Case-by-case non-commercial academic access; not downloaded or assumed authorized. |
| Text emotion / synthetic vishing sources | Web search results reviewed for task match | Excluded: text sentiment or synthetic dialogue labels do not provide real acoustic telephone emotion ground truth. |

No accessible, purpose-permitted, reviewed Moroccan telephone emotion corpus was identified among these checked sources. This is a search result, not a claim no such corpus exists. French real-call transfer remains unmeasured.

## Pinned acquisition and selection

CREMA-D revision `1658cd342dff90010aa843eaeebd53610a08b1dc`; MDER mirror revision `4a9e6b02b78516ac50109cc2816386ac699aff95`. Deterministic metadata-first selection chose four records per class per source, preferring distinct source speaker keys within each class. Five English source speaker keys and fifteen Darija source keys occur in the selected data. Those keys are not independently verified identities and do not establish cross-source speaker disjointness or pretraining exclusion.

Selection preceded model inference. Source checksums were compared with Git LFS / Hugging Face LFS metadata at the pinned revisions. Source CSVs/license/card and a private manifest retain lineage, per-record rights/label notes and retention. Public evidence contains hashes/pseudonymous keys and aggregate metrics, not audio or transcripts. A checksum stored beside data is not independently immutable.

The MDER mirror's test metadata lacks an adult neutral example satisfying the selected window bound. To avoid silently inventing labels or including minors, selection used the full metadata.csv and explicitly records that it is not a mirror-test-only experiment. There was no project training or tuning on these clips, but independence from model/vendor pretraining is unknown. Do not call this an untouched promotion test.

Direct local Mendeley requests encountered certificate validation failure; no certificate bypass was used. Licensing was verified on the original record via web access, while the bounded audio subset was acquired from the pinned mirror. A decoding spelling error (`utf8-sig`) in intake was corrected to `utf-8-sig` before the successful acquisition; early partial files remained local. Completed snapshots are now refused before acquisition on rerun.

# Makefile for  ssusearch
# key parameters


### path of sequence file if not defined in CMD line. 
Seqfile?=/mnt/scratch/tg/g/dataForPaper/RNA/jobs/cluster/ssusearch/test/data/1c.fa
Cpu?=1
Phred?=33
# tools, dirs, etc
Script_dir?=./scripts
Flash?=/mnt/home/guojiaro/Documents/software/QC/FLASH/flash
Flash_flags?=-m 10 -M 120 -x 0.08 -r 140 -f 250 -s 25 -d . -t 1 -p $(Phred)
Hmmsearch?=hmmsearch
Mothur?=/mnt/home/guojiaro/Documents/software/mothur/Mothur.source/./mothur

Gene?=ssu

# refs
Hmm?=../SSUsearch_db/Hmm.ssu.hmm
Ali_template?=../SSUsearch_db/Ali_template.silva_ssu.fasta
Gene_model_org?=../SSUsearch_db/Gene_model_org.16s_ecoli_J01695.fasta

override Seqfile:=$(realpath $(Seqfile))
Seqfile_name:=$(notdir $(Seqfile))
Seqfile_name_parts:=$(subst ., ,	$(Seqfile_name))

#Tag?=$(word 1,$(Seqfile_name_parts))
Tag?=dummy

# internal parameters
Qc_file?=$(Tag).qc
Hmmsearch_file?=$(Tag).qc.$(Gene)

TERM?=linux

ssusearch_no_qc: no_qc_setup hmmsearch mothur_align
ssusearch_se_qc: se_qc_setup hmmsearch mothur_align
ssusearch_pe_qc: pe_qc_setup hmmsearch mothur_align
align_only: align_only_setup mothur_align

### this target is for testing search
search_only: no_qc_setup hmmsearch

.PHONY: no_qc_setup se_qc_setup pe_qc_setup align_only_setup \
	hmmsearch mothur_align clean \
	ssusearch_no_qc ssusearch_se_qc ssusearch_pe_qc align_only search_only

no_qc_setup: $(Seqfile)
	Realfile=$(realpath $(Seqfile)) \
	&& if file $$Realfile | grep -q "gzip compressed data" ; \
	   then zcat $(Seqfile) > $(Qc_file); \
	   elif file $$Realfile | grep -q "bzip2 compressed data"; \
	   then bzcat $(Seqfile) > $(Qc_file); \
	   else ln -sf $(Seqfile) $(Qc_file); \
	   fi;

align_only_setup: $(Seqfile)
	ln -sf $(Seqfile) $(Hmmsearch_file)

pe_qc_setup: $(Seqfile)
	@echo "*** Starting read quality control and pair end merging"
	python $(Script_dir)/quality-trim-sep-pe.py $(Phred) $(Seqfile) \
		$(Tag)
	$(Flash) $(Tag).1 $(Tag).2 \
		$(Flash_flags) -o $(Tag) | \
	tee $(Tag.flash.report)

	-(rm $(Tag).1 $(Tag).2)
	cat $(Tag).{extendedFrags,notCombined_1,notCombined_2}.fastq \
		> $(Tag).afterQC.fastq

	python $(Script_dir)/fq2fa.py $(Tag).aftermerge.fastq \
		$(Qc_file) \
	|| { rm $(Qc_file) && exit 1; }

	-(rm $(Tag).{extendedFrags,notCombined_1,notCombined_2}.fastq)


se_qc_setup: $(Seqfile)
	@echo "*** Starting read quality control and pair end merging"
	python $(Script_dir)/quality-trim-se.py $(Phred) $(Seqfile) \
		$(Tag).afterQC.fastq

	python $(Script_dir)/fq2fa.py $(Tag).afterQC.fastq \
		$(Qc_file) \
	|| { rm -f $(Qc_file) && exit 1; }

hmmsearch: $(Qc_file)
	@echo
	@echo "*** Starting hmmsearch"
	time $(Hmmsearch) --incE 10 --incdomE 10 --cpu $(Cpu) \
		-A $(Tag).qc.$(Gene).sto \
		-o $(Tag).qc.$(Gene).hmmout \
		--tblout $(Tag).qc.$(Gene).hmmtblout \
		--domtblout $(Tag).qc.$(Gene).hmmdomtblout \
		$(Hmm) $(Tag).qc
	@echo "hmmsearch done.."
	python $(Script_dir)/get-seq-from-hmmout.py \
		$(Tag).qc.$(Gene).hmmdomtblout \
		$(Tag).qc.$(Gene).sto \
		$(Tag).qc.$(Gene) \
	|| { rm -f $(Tag).qc.$(Gene) && exit 1; }
	rm -f $(Tag).qc
	@echo "hmm filter and MSA conversion done.."

mothur_align: $(Hmmsearch_file)
	@echo
	@echo "*** Starting mothur align"
	cat $(Gene_model_org) $(Hmmsearch_file) > \
		$(Tag).qc.$(Gene).RFadded

	# mothur does not allow tab between its flags, thus no indents here
	time $(Mothur) "#align.seqs(\
	candidate=$(Tag).qc.$(Gene).RFadded, \
	template=$(Ali_template), threshold=0.5, \
	flip=t, processors=$(Cpu))"
	@rm -f mothur.*.logfile

	python $(Script_dir)/mothur-align-report-parser.py \
		$(Tag).qc.$(Gene).align.report \
		$(Tag).qc.$(Gene).align \
		$(Tag).qc.$(Gene).align.filter \
	|| { rm -f $(Tag).qc.$(Gene).align.filter && exit 1; }

clean:
	-(rm -f \
	$(filter-out %.filter %.filter.fa %.qc %.taxonomy $(Tag),\
	$(wildcard $(Tag)*)))

	@echo "*** Files kept after clean:"
	@ls

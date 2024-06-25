from django.contrib.auth.models import AbstractUser
from django.db import models

SEPERATION_TECHNIQUE = (('LC', 'LC'), ('CE', 'CE'), ('GC', 'GC'), ('IM', 'IM'),)
#
STATIONARY_PHASE = (('RP', 'RP'), ('HILIC', 'HILIC'), ('IE', 'IE'), ('SEC', 'SEC'),)
#
EXPERIMENT_TYPE = (('MS', 'MS'), ('LCMS', 'LCMS'), ('LCMSn', 'LCMSn'), ('TIMSPASEF', 'TIMSPASEF'),)
#
ACQUISITION_TYPE = (('DDA', 'DDA'), ('DIA', 'DIA'), ('MRM', 'MRM'), ('SRM', 'SRM'),)
#
INSTRUMENT_TYPE = (('Quadrupole', 'Quadrupole'), ('TOF', 'TOF'), ('IT', 'IT'), ('FTR', 'FTR'),)
#
VENDOR_TYPE = (
    ('ThermoFischer', 'ThermoFischer'), ('ABSCIEX', 'ABSCIEX'), ('BRUIKER', 'BRUIKER'), ('Waters', 'Waters'),)
#
LIPID_CATEGORIES = (
    ('FattyAcyls', 'FattyAcyls'), ('GlycerolLipids', 'GlycerolLipids'),
    ('GlycerolPhospholipids', 'GlycerolPhospholipids'),
    ('Sterols', 'Sterols'), ('Prenols', 'Prenols'), ('Sphingolipids', 'Sphingolipids'))

PIPELINE_INITIALIZING = 'initializing'
PIPELINE_CONVERTING = 'converting'
PIPELINE_EXTRACTING = 'database search'
PIPELINE_COMPLETED = 'completed'
LIPIDOMICS_PIPELINE = 'Lipidomics'
PROTEOMICS_PIPELINE = 'Proteomics'
GLYCOMICS_PIPELINE = 'Glycomics'
SEARCH_ENGINE = 'OMMSSA'
SEARCH_TECHNIQUE = 'Database'
SEARCH_MODIFICATIONS = 'All'
VALIDATION_ENGINE = 'Percolator'
PROCESSING_METHODS = 'All'
ADDUCT_WHITELIST = [' [M+H]+', '[M+Na]+', '[M+NH4]+', '[M-H]-', '[M+HCOO]-']
LIPIDS_WHITELIST = ['Sphingomyelins (SM)', 'Cholesterol esters (CE)', ' Glycerophosphocholines (PC)',
                    'Glycerophosphoethanolamines (PE)', 'Tri(acyl|alkyl)glycerols (TG)', 'Di(acyl|alkyl)glycerols (DG)']
LIPID_DATABASE = ['LIPIDMAPS', 'COMP DB']
FILE_TYPE = ['.RAW', '.mzML' '.zip']


class LTUser(AbstractUser):
    pass


class PipelineFile(models.Model):
    pipeline = models.ForeignKey('Pipeline', on_delete=models.CASCADE)
    file = models.FileField(null=True)


class Pipeline(models.Model):
    token = models.CharField(max_length=255)
    status = models.CharField(max_length=255, default=PIPELINE_INITIALIZING)
    searchtechnique = models.CharField(max_length=255, choices=SEARCH_TECHNIQUE)
    instrumentType = models.CharField(max_length=255, choices=INSTRUMENT_TYPE)
    seperationTechnique = models.CharField(max_length=255, choices=SEPERATION_TECHNIQUE)
    stationaryPhase = models.CharField(max_length=255, choices=STATIONARY_PHASE)
    experimentType = models.CharField(max_length=255, choices=EXPERIMENT_TYPE)
    vendorType = models.CharField(max_length=255, choices=VENDOR_TYPE)
    results_file = models.FileField(null=True)
    summary_file = models.FileField(null=True)
    ftpserver_url = models.URLField(max_length=200, default='')
    filetype = models.CharField(max_length=255, choices=FILE_TYPE)

    class Meta:
        abstract = True


class LipidomicsPipeline(Pipeline):
    lipidCategories = models.CharField(max_length=255, choices=LIPIDS_WHITELIST)
    adductswhitelist = models.CharField(max_length=255, choices=ADDUCT_WHITELIST)
    lipiddatabase = models.CharField(max_length=255, choices=LIPID_DATABASE)


class ProteomicsPipeline(Pipeline):
    fasta_database = models.FileField(null=True)
    validationengine = models.CharField(max_length=255, choices=VALIDATION_ENGINE)
    searchengine = models.CharField(max_length=255, choices=SEARCH_ENGINE)
    modifications = models.CharField(max_length=255, choices=SEARCH_MODIFICATIONS)

import os
import random
import shutil
import string
import subprocess
import threading
import ursgal
from django.core.files import File
from django.http import HttpResponseForbidden
from rest_framework.response import Response
from rest_framework.views import APIView
from lipitum.models import LipidomicsPipeline, ProteomicsPipeline, PipelineFile
from lipitum.nativeconverter.mzml import *


analyses_dir = 'C:/Users/kunda/Documents/Bioinformatics/Projects/multiomics-pipeline/lipitum-backend/media'

suggestion_cache = {}


# class ProcessView(APIView):
#
#     def get(self, request):
#         token = request.GET.get('token')
#         if token is None:
#             return HttpResponseForbidden()
#
#         process = ProcessStream.objects.get(token=token)
#
#         return Response({
#             'status': process.status,
#         })
#
#     def post(self, request):
#         if request.method == 'POST':
#             pipeline_type = request.POST.get('pipeline_type')
#
#             if 'file' not in request.FILES:
#                 return None
#             token = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))
#
#             process = ProcessStream()
#             process.token = token
#             process.pipeline_type = pipeline_type
#             process.save()
#             thread = None
#             if pipeline_type == 'lipidomics':
#                 thread = threading
#             elif pipeline_type == 'proteomics':
#
#             thread.start()
#
#             return Response({
#                 'token': token,
#             })


def get_pipeline(request, pipeline_class):
    token = request.GET.get('token')
    if token is None:
        return HttpResponseForbidden()

    pipeline = pipeline_class.objects.get(token=token)
    if pipeline is None:
        return HttpResponseForbidden()

    return Response({
        'status': pipeline.status,
    })


def create_pipeline(request, pipeline_class):
    token = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))

    pipeline = pipeline_class()
    pipeline.token = token
    pipeline.save()

    # for f in request.FILES.getlist('file'):
    #     raw_file = PipelineFile()
    #     raw_file.pipeline = pipeline
    #     raw_file.file = f
    #     raw_file.save()

    return pipeline, token


def upload_file_or_process(request, pipeline_class, pipeline_function):
    token = request.GET.get('token')
    if token is None:
        return HttpResponseForbidden()

    pipeline = pipeline_class.objects.get(token=token)
    if pipeline is None:
        return HttpResponseForbidden()

    if 'file' not in request.FILES:
        thread = threading.Thread(target=pipeline_function, daemon=True)
        thread.start()
    else:
        pipeline_file = PipelineFile()
        pipeline_file.file = request.FILES['file']
        pipeline_file.pipeline = pipeline
        pipeline_file.save()


# UPLOAD PROCESS:
# 1. POST to http://localhost:8000/pipeline/lipidomics to create the pipeline, you'll receive {token: <token>}
# 2. Then, PUT a file to http://localhost:8000/pipeline/lipidomics?token=<token> (using the token you received before)
# 3. Finally, to start processing, PUT again to http://localhost:8000/pipeline/lipidomics?token=<token>, this time without a file


class LipidomicsView(APIView):

    def get(self, request):
        return get_pipeline(request, LipidomicsPipeline)

    def post(self, request):
        # ProcessView.post(self, request)

        pipeline, token = create_pipeline(request, LipidomicsPipeline)
        if not pipeline:
            return None

        lipidCategories = request.POST.get('lipidCategories')
        adductswhitelist = request.POST.get('adductswhitelist')
        userddatop = request.POST.get('userddatop')
        pipeline.lipidCategories = lipidCategories
        pipeline.adductswhitelist = adductswhitelist
        pipeline.save()

        return Response({
            'token': token,
        })

    # This endpoint expects `?token=<token>` to identify the pipeline
    def put(self, request):
        upload_file_or_process(request, LipidomicsPipeline, process_lipidomics)


class ProteomicsView(APIView):

    def get(self, request):
        return get_pipeline(request, ProteomicsPipeline)

    def post(self, request):
        pipeline, token = create_pipeline(request, ProteomicsPipeline)
        if not pipeline:
            return None

        fasta_database = request.POST.get('fasta_database')
        validationengine = request.POST.get('validationengine')
        searchengine = request.POST.get('searchengine')
        modifications = request.POST.get('modifications')
        pipeline = ProteomicsPipeline()
        pipeline.modifications = modifications
        pipeline.fasta_database = fasta_database
        pipeline.validationengine = validationengine
        pipeline.searchengine = searchengine
        pipeline.save()

        return Response({
            'token': token,
        })

    def put(self, request):
        upload_file_or_process(request, ProteomicsPipeline, process_proteomics)


def process_lipidomics(pipeline):
    pipeline.status = 'converting'
    pipeline.save()

    base_name = f'{analyses_dir}/{pipeline.token}'
    output_folder = base_name + '_convert'
    input_folder = base_name + '_input'
    os.mkdir(input_folder)
    os.mkdir(output_folder)

    raw_files = PipelineFile.objects.filter(pipeline=pipeline).all()
    threads = []
    for raw_file in raw_files:
        thread = threading.Thread(target=process_lipidomics_individual,
                                  args=(raw_file, input_folder, output_folder),
                                  daemon=True)
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    # TODO:
    #  Now that all threads have finished, the result files should reside in the output_path folder
    #  You can now apply some logic on these files to merge them into one result file for later display in the
    #  frontend.

    # if pipeline.raw_file.path.lower().endswith('.raw'):
    #     raw_convert(input_folder, convert_folder)
    #     pipeline.status = 'extracting'
    #     pipeline.save()
    #
    #     extract_file(
    #         'C:/Users/kunda/Documents/Computational-Lipidomics/Publication/lipitum-backend/lipitum/targetlist',
    #         convert_folder,
    #         base_name,
    #     )
    #
    #     results_name = base_name + '_results.tab'
    #
    #     calculate_metrics(results_name)
    #
    #     pipeline.results_file = File(open(results_name))
    #     pipeline.status = 'finished'
    #     pipeline.save()
    #
    # elif pipeline.raw_file.path.lower().endswith('.mzml'):
    #     convert(input_folder, convert_folder)
    #
    #     pipeline.status = 'extracting'
    #     results_name = base_name + '_' + 'usr_ms1_xic_df' + '_' + '.tab'
    #     result = pd.read_csv(results_name, sep="\t")
    #     bulk_structure_search(result, convert_folder)
    #     pipeline.save()
    #
    #     pipeline.status = 'finished'
    #     pipeline.save()


def process_lipidomics_individual(pipeline_file, input_path, output_path):
    file_path = input_path + '/' + pipeline_file.name
    shutil.copyfile(pipeline_file.path, file_path)

    # TODO:
    #  Apply the processing for a single file on file_path
    #  Then, store the results in the output_path folder


def extract_file(tpath, mspath, opath):
    java_exec = 'C:/Program Files/Java/jdk-14.0.1/bin/java.exe'
    java_program = 'C:/Users/kunda/Documents/Computational-Lipidomics/Publication/lipitum-backend/lipitum/extractor/classes'

    cmd = [java_exec, '-cp', java_program, 'Extraction.Main', tpath, mspath, opath]

    print(' '.join(cmd))

    print(subprocess.call(cmd))


def calculate_metrics(filename):
    result = pd.read_csv(filename, sep="\t")
    result_filtered = result[result['Intensity'] > 1000000]
    result_filtered = result_filtered[
        ["RetentionTime", "RAW_ID", "Polarity", "Lipid species", "Target m/z", "Measured m/z", "Intensity",
         "Lipid class", "ppmerror", "m/z offset", "Lipid category", "Adduct", "C index of lipid species",
         "DB index of lipid species", ]]
    result_filtered = result_filtered.rename(
        columns={'Target m/z': 'TargetMass', 'Measured m/z': 'Mass', 'Lipid class': 'LipidClass',
                 'C index of lipid species': 'Length', 'DB index of lipid species': 'DoubleBonds',
                 'm/z offset': 'mzoffset', 'Lipid species': 'LipidSpecies', 'Lipid category': 'LipidCategory'})
    result_filtered['error'] = mass_diff(result_filtered['Mass'].values, result_filtered['TargetMass'].values)
    result_filtered.to_csv(filename, sep="\t", index=False)


def process_proteomics(pipeline):
    pipeline.status = 'converting'
    pipeline.save()

    base_name = f'{analyses_dir}/{pipeline.token}'
    convert_folder = base_name + '_convert'
    input_folder = base_name + '_input'
    os.mkdir(input_folder)

    shutil.copyfile(pipeline.raw_file.path, input_folder + '/' + pipeline.raw_file.name)
    os.mkdir(convert_folder)

    uc = ursgal.UController(params={"enzyme": "trypsin", "decoy_generation_mode": "reverse_protein", })
    raw_files = [os.path.join(input_folder, file) for file in os.listdir(input_folder) if file.endswith(".mzML")]
    pipeline.status = 'extracting'
    pipeline.save()
    fasta_file = 'C:/Users/kunda/Documents/Computational-Lipidomics/Publication/lipitum-backend/media/fasta_files/BSA.fasta'
    target_decoy_database = uc.execute_misc_engine(input_file=fasta_file, engine="generate_target_decoy_1_0_0")
    search_engine = ["omssa"]
    mass_spectrometer = 'QExactive+'
    validation_engines = ["percolator_2_08", "qvality"]
    all_mods = ["C,fix,any,Carbamidomethyl", "M,opt,any,Oxidation", "*,opt,Prot-N-term,Acetyl"]
    params = {
        "database": target_decoy_database,
        "modifications": all_mods,
        "csv_filter_rules": [
            ["Is decoy", "equals", "false"],
            ["PEP", "lte", 0.01],
        ],
    }

    uc = ursgal.UController(profile=mass_spectrometer, params=params)

    for validation_engine in validation_engines:
        result_files = []
        for spec_file in raw_files:
            validated_results = []
            for search_engine in search_engine:
                unified_search_results = uc.search(input_file=spec_file, engine=search_engine)
                validated_csv = uc.validate(input_file=unified_search_results, engine=validation_engine, )
                validated_results.append(validated_csv)

            validated_results_from_all_engines = uc.execute_misc_engine(input_file=validated_results,
                                                                        engine="merge_csvs_1_0_0", )
            filtered_validated_results = uc.execute_misc_engine(input_file=validated_results_from_all_engines,
                                                                engine="filter_csv_1_0_0", )
            result_files.append(filtered_validated_results)

        results_all_files = uc.execute_misc_engine(input_file=result_files, engine="merge_csvs_1_0_0", )

        pipeline.status = 'finished'
        pipeline.save()

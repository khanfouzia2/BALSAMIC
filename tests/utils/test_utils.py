import json
import pytest
from pathlib import Path

from BALSAMIC.utils.cli import get_ref_path
from BALSAMIC.utils.cli import SnakeMake
from BALSAMIC.utils.cli import iterdict
from BALSAMIC.utils.cli import sbatch
from BALSAMIC.utils.cli import get_packages
from BALSAMIC.utils.cli import get_package_split
from BALSAMIC.utils.cli import get_snakefile
from BALSAMIC.utils.cli import createDir
from BALSAMIC.utils.rule import get_chrom
from BALSAMIC.utils.rule import get_vcf
from BALSAMIC.utils.rule import get_sample_type
from BALSAMIC.utils.rule import get_conda_env
from BALSAMIC.utils.rule import get_picard_mrkdup
from BALSAMIC.utils.rule import get_script_path

def test_get_ref_path(config_files):
    # GIVEN a sample json file path
    test_ref = config_files['test_reference']

    # WHEN giving a path for json file,
    test_ref_json = get_ref_path(test_ref)

    # THEN It will read the file and return a dict with updated absolute path
    assert isinstance(test_ref_json, dict)
    assert test_ref_json['path']['genomefa'].startswith('/')


def test_iterdict(config_files):
    """ GIVEN a dict for iteration """
    test_dict = json.load(open(config_files['test_reference'], 'r'))

    # WHEN passing dict to this function
    dict_gen = iterdict(test_dict)

    # THEN it will create dict generator, we can iterate it, get the key, values as string
    for key, value in dict_gen:
        assert isinstance(key, str)
        assert isinstance(value, str)

def test_sbatch():
    # GIVEN values for sbatch command
    sbatch_cmd = sbatch()
    sbatch_cmd.account = "development"
    sbatch_cmd.dependency = "afterok:12345"
    sbatch_cmd.error = "test_job.err"
    sbatch_cmd.output = "test_job.out"
    sbatch_cmd.mail_type = "FAIL"
    sbatch_cmd.mail_user = "john.doe@example.com"
    sbatch_cmd.ntasks = "2"
    sbatch_cmd.qos = "low"
    sbatch_cmd.time = "01:00:00"
    sbatch_cmd.script = "example_script.sh" 

    # WHEN sbatch command is built
    sbatch_cmd = sbatch_cmd.build_cmd()

    # THEN sbatch command string is constructed
    assert isinstance(sbatch_cmd, str)
    assert sbatch_cmd == 'sbatch --account "development" --dependency "afterok:12345" --error "test_job.err" --output "test_job.out" --mail-type "FAIL" --mail-user "john.doe@example.com" --ntasks "2" --qos "low" --time "01:00:00" example_script.sh'   

def test_snakemake_local():
    # GIVEN required params
    snakemake_local = SnakeMake()
    snakemake_local.working_dir = "/tmp/snakemake"
    snakemake_local.snakefile = "worflow/variantCalling_paired"
    snakemake_local.configfile = "sample_config.json"
    snakemake_local.run_mode = "local"
    snakemake_local.forceall = True

    # WHEN calling the build command
    shell_command = snakemake_local.build_cmd()

    # THEN it will contruct the snakemake command to run
    assert isinstance(shell_command, str)
    assert "worflow/variantCalling_paired" in shell_command
    assert "sample_config.json" in shell_command
    assert "/tmp/snakemake" in shell_command
    assert "--dryrun" in shell_command
    assert "--forceall" in shell_command


def test_snakemake_slurm():
    # GIVEN required params
    snakemake_slurm = SnakeMake()
    snakemake_slurm.sample_name = "test_sample"
    snakemake_slurm.working_dir = "/tmp/snakemake"
    snakemake_slurm.snakefile = "worflow/variantCalling_paired"
    snakemake_slurm.configfile = "sample_config.json"
    snakemake_slurm.run_mode = "slurm"
    snakemake_slurm.cluster_config = "cluster_config.json"
    snakemake_slurm.scheduler = "sbatch.py"
    snakemake_slurm.log_path = "logs/"
    snakemake_slurm.script_path = "scripts/"
    snakemake_slurm.result_path = "results/"
    snakemake_slurm.qos = "normal"
    snakemake_slurm.account = "development"
    snakemake_slurm.mail_type = "FAIL"
    snakemake_slurm.mail_user = "john.doe@example.com"
    snakemake_slurm.sm_opt = ("containers", )
    snakemake_slurm.run_analysis = True

    # WHEN calling the build command
    shell_command = snakemake_slurm.build_cmd()

    print(shell_command)
    # THEN constructing snakecommand for slurm runner
    assert isinstance(shell_command, str)
    assert "worflow/variantCalling_paired" in shell_command
    assert "sample_config.json" in shell_command
    assert "/tmp/snakemake" in shell_command
    assert "--dryrun" not in shell_command
    assert "sbatch.py" in shell_command
    assert "test_sample" in shell_command
    assert "containers" in shell_command


def test_get_packages(conda):
    # GIVEN a conda yaml file
    balsamic_yaml = conda['balsamic-base']

    # WHEN passing conda yaml file to get_packages
    packages = get_packages(balsamic_yaml)

    # THEN It should return all tools(packages) in that yaml file
    assert any("snakemake" in tool for tool in packages)
    assert any("python=3" in tool for tool in packages)


def test_get_pacakges_error(conda):
    with pytest.raises(Exception, match=r"No such file or directory"):
        # GIVEN a wrong path for config yaml file
        invalid_yaml = "/tmp/balsamic.yaml"

        # WHEN passing this invalid path into get_packages
        # THEN It shoud raise the file not found error
        assert get_packages(invalid_yaml)


def test_get_package_split(conda):
    # GIVEN a list of conda config yaml file paths
    yamls = conda.values()

    # WHEN giving this list of yamls to get_packaged split
    packages = get_package_split(yamls)

    # THEN It should return a dictionary with tools information
    assert isinstance(packages, dict)
    assert "bwa" in packages
    assert "bcftools" in packages
    assert "cutadapt" in packages
    assert "fastqc" in packages

def test_get_script_path():
    # GIVEN list of scripts
    custom_scripts = ["refseq_sql.awk"]

    # WHEN asking to get path for the script
    for script in custom_scripts:
        # THEN assert full path for script
        assert get_script_path(script).startswith('/')
        
        # THEN assert if script file exists
        assert Path(get_script_path(script)).is_file()

def test_get_snakefile():
    # GIVEN analysis_type for snakemake workflow
    analysis_types = ["paired", "single", "qc", "paired_umi", "single_umi"]

    # WHEN asking to see snakefile for paired
    for analysis_type in analysis_types:
        snakefile = get_snakefile(analysis_type)

        # THEN it should return the snakefile path
        assert snakefile.startswith('/')
        if analysis_type != 'qc':
            assert "BALSAMIC/workflows/VariantCalling_" + analysis_type in snakefile
        else:
            assert "BALSAMIC/workflows/Alignment" in snakefile
        # THEN assert file exists
        assert Path(snakefile).is_file()


def test_get_chrom(config_files):
    # Given a panel bed file
    bed_file = config_files["panel_bed_file"]

    # WHEN passing this bed file
    chrom = get_chrom(bed_file)

    # THEN It should return list of chrom presents in that bed file
    for chr_num in range(1, 21):
        assert str(chr_num) in chrom


def test_get_vcf(sample_config):
    # GIVEN a sample_config dict, varinat callers list
    variant_callers = ['mutect', 'vardict', 'manta']

    # WHEN passing args to that function
    vcf_list = get_vcf(sample_config, variant_callers,
                       [sample_config["analysis"]["sample_id"]])

    # THEN It should return the list of vcf file names
    assert any("mutect" in vcf_name for vcf_name in vcf_list)
    assert any("vardict" in vcf_name for vcf_name in vcf_list)
    assert any("manta" in vcf_name for vcf_name in vcf_list)


def test_get_sample_type(sample_config):
    # GIVEN a sample_config dict, bio_type as tumor
    bio_type = 'tumor'

    # WHEN calling get_sample_type with bio_type
    sample_id = get_sample_type(sample_config["samples"], bio_type)

    # THEN It should return the tumor samples id
    assert sample_id == ['S1_R']


# def test_get_conda_env(sample_config):
#     # GIVEN a balsamic_env yaml file path
#     balsamic_env = "BALSAMIC_env.yaml"

#     # WHEN passing pkg name with this yaml file
#     conda_env = get_conda_env(balsamic_env, 'ensembl-vep')

#     # THEN It should return the conda env which has that pkg
#     assert "Cancer-vep" in conda_env


def test_get_picard_mrkdup(sample_config):
    # WHEN passing sample_config
    picard_str = get_picard_mrkdup(sample_config)

    # THEN It will return the picard str as rmdup
    assert "rmdup" == picard_str

def test_createDir(tmp_path):
    # GIVEN a directory path
    # WHEN directory path is not yet created 
    test_new_dir = tmp_path / "new_dir"
    
    # THEN it should create and return dir name
    test_new_dir_created = createDir(str(test_new_dir))
    assert test_new_dir_created == str(tmp_path / "new_dir")
    assert Path(test_new_dir_created).is_dir()

    # GIVEN a directory path
    test_log_dir = tmp_path / "existing_dir"
    
    # WHEN directory path exists 
    test_log_dir.mkdir()
    
    # THEN it should return log_dir name incremented
    test_log_dir_created = createDir(str(test_log_dir), []) 
    assert test_log_dir_created == str(tmp_path / "existing_dir.1")
    assert Path(test_log_dir_created).is_dir()

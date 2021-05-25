import tempset
from tempset import batch_process_idf, analyze_results


def testing():
    eplus_file = "/people/rahm312/temp-setpoints/tempset/json/eplus_params.json"
    batch_file = "/people/rahm312/temp-setpoints/tempset/json/batch_params.json"
    param_file = "/people/rahm312/temp-setpoints/tempset/json/htgsetp_params.json"
    output_dir = "/people/rahm312/temp-setpoints/tempset/output/"

    batch_process_idf(eplus_config=eplus_file,
                      param_json=param_file,
                      batch_param=batch_file,
                      htgsetpoint_params_csv_output=None,
                      output_dir=output_dir,
                      write_logfile=False,
                      idf_file=None)

    return None


def analyze():
    summary_file = '/people/rahm312/temp-setpoints/tempset/data/electric/summary.csv'
    param_file = '/people/rahm312/temp-setpoints/tempset/data/electric/htgsetp_params_electric.csv'
    case_study = 'I'
    fig_dir = '/people/rahm312/temp-setpoints/tempset/figures/prob_dist'
    fig_ext = '.svg'
    output_dir = "/people/rahm312/temp-setpoints/tempset/output/"

    analyze_results(
        summary_file=summary_file,
        param_file=param_file,
        case_study=case_study,
        fig_dir=fig_dir,
        fig_ext=fig_ext,
        out_dir=output_dir
    )

    return None


if __name__ == "__main__":
    #testing()
    analyze()

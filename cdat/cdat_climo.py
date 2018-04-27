import os
import glob
import cdutil
import cdms2
import numpy
import MV2

value = 0
cdms2.setNetcdfShuffleFlag(value) ## where value is either 0 or 1
cdms2.setNetcdfDeflateFlag(value) ## where value is either 0 or 1
cdms2.setNetcdfDeflateLevelFlag(value) ## where value is a integer between 0 and 9 included


def what_season(fnm):
    """
    Given a file in the format:
        case_id.cam.h0.<year>.<month>.nc
    return the season that it belongs to.
    """
    month_to_season = {
        "01": "DJF",
        "02": "DJF",
        "03": "MAM",
        "04": "MAM",
        "05": "MAM",
        "06": "JJA",
        "07": "JJA",
        "08": "JJA",
        "09": "SON",
        "10": "SON",
        "11": "SON",
        "12": "DJF"
    }

    month = fnm[-5:-3]
    return month_to_season[month] if month in month_to_season else None


def get_input_files_from_climo(args):
    """
    Given the input arguments, return the list of files
    to be opened to create a climatology.
    """
    files = []

    # Use the explicitly defined files from the user
    if args.input_files:
        for input_file in args.input_files:
            input_dir = os.path.expanduser(args.input_dir)
            pth = os.path.join(input_dir, input_file)
            for file_found in glob.glob(pth):
                files.append(file_found)

    else:
        # Otherwise, use start and end year, along with case, to get the files
        s_yr, e_yr, case = args.start_yrs, args.end_yrs, args.case

        # Add the last month of the last year
        fnm = '{}.cam.h0.{:04d}-12.nc'.format(case, s_yr-1)
        fnm = os.path.join(args.input_dir, fnm)
        if os.path.exists(fnm):
            files.append(fnm)

        # Add everything from s_yr to e_yr.
        # +1 is because e_yr is inclusive.
        for yr in range(s_yr, e_yr+1):
            # glob only gets files that exist, so no need to check for that
            found_files = glob.glob(os.path.join(args.input_dir, '{}.cam.h0.{:04d}*nc'.format(case, yr)))
            files.extend(found_files)

        # Remove the last file, which is *h0.e_yr-12.nc, since we don't need the 12th month
        if len(files) >= 1:
            files.pop()

    print('Using files:')
    for f in files:
        print(f)
    
    # Check that the required number of files were given
    expected_files = 12*(e_yr-s_yr+1)
    if len(files) != expected_files:
        msg = 'We expected {} files, but only found {} for the years from {} to {}.'
        raise Exception(msg.format(expected_files, len(files), s_yr, e_yr))

    return files

def run(args):
    #input_dir = '/p/user_pub/work/E3SM/1_0/piControl/1deg_atm_60-30km_ocean/atmos/129x256/model-output/mon/ens1/v1'
    #input_dir = '~/climo_timeseries_data'
    #output_dir = '~/e3sm_diags_timeseries'
    input_dir = args.input_dir
    output_dir = args.output_dir
    #start_year = 2
    #end_year = 2
    start_year = args.start_yrs
    end_year = args.end_yrs
    # variables = ['FLNT', 'FSNTOAC']
    variables = args.vars
    monthly_files = get_input_files_from_climo(args)
    #print(args)
    #print(input_files)
    #quit()


    # os.path.expanduser() is for paths with `~`
    # input_dir = os.path.abspath(os.path.expanduser(input_dir))
    # output_dir = os.path.abspath(os.path.expanduser(output_dir))
    output_dir = os.path.join(output_dir, 'cdat_climo_results')

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    #start_year = '{:04d}'.format(start_year)
    #end_year = '{:04d}'.format(end_year)


    # h0_file = '20180129.DECKv1b_piControl.ne30_oEC.edison.cam.h0.0002-12.nc'
    # for climo:
    # ncrcat of all of these files, actually creates a file with all of the stuff combined.
    # or use cdscan for CDAT stuff
    '''
    monthly_files = [
    '20180129.DECKv1b_piControl.ne30_oEC.edison.cam.h0.0001-12.nc',
    '20180129.DECKv1b_piControl.ne30_oEC.edison.cam.h0.0002-01.nc',
    '20180129.DECKv1b_piControl.ne30_oEC.edison.cam.h0.0002-02.nc',
    '20180129.DECKv1b_piControl.ne30_oEC.edison.cam.h0.0002-03.nc',
    '20180129.DECKv1b_piControl.ne30_oEC.edison.cam.h0.0002-04.nc',
    '20180129.DECKv1b_piControl.ne30_oEC.edison.cam.h0.0002-05.nc',
    '20180129.DECKv1b_piControl.ne30_oEC.edison.cam.h0.0002-06.nc',
    '20180129.DECKv1b_piControl.ne30_oEC.edison.cam.h0.0002-07.nc',
    '20180129.DECKv1b_piControl.ne30_oEC.edison.cam.h0.0002-08.nc',
    '20180129.DECKv1b_piControl.ne30_oEC.edison.cam.h0.0002-09.nc',
    '20180129.DECKv1b_piControl.ne30_oEC.edison.cam.h0.0002-10.nc',
    '20180129.DECKv1b_piControl.ne30_oEC.edison.cam.h0.0002-11.nc',
    ]
    '''

    cdutil_seasons = {}
    cdutil_seasons['ANN'] = cdutil.ANNUALCYCLE
    cdutil_seasons['DJF'] = cdutil.DJF
    cdutil_seasons['MAM'] = cdutil.MAM
    cdutil_seasons['JJA'] = cdutil.JJA
    cdutil_seasons['SON'] = cdutil.SON

    #variables = []
    seasons = ['ANN', 'DJF', 'MAM', 'JJA', 'SON']
    #seasons = ['DJF', 'MAM', 'JJA', 'SON']

    output_vars = {}  # a dict var_name: cdms2.TransientVariable

    first_file_pth = monthly_files[0]
    shape = ()
    with cdms2.open(first_file_pth) as f:
        if variables == []:
            variables = list(f.variables.keys())

        print('Using variables: {}'.format(variables))
        shape = f(variables[-1]).shape
        '''
        # Create a TransientVariables of the valid size for each var
        for v in variables:
            shape = f(v).shape
            print('{}: {}'.format(v, shape))
            output_vars[v] = MV2.array(numpy.zeros(shape))
        '''

    '''
    for s in seasons:
        # ex: 20180129.DECKv1b_piControl.ne30_oEC.edison_MAM_016603_017005_climo.nc
        case = '20180129.DECKv1b_piControl.ne30_oEC.edison'
        fnm = '{}_{}_{}01_{}12_climo.nc'.format(case, s, start_year, end_year)
        output_files[s] = cdms2.open(fnm, 'w')
    '''

    # Initalize the output variables, one for each season
    for s in seasons:
        output_vars[s] = MV2.array(numpy.zeros(shape))



    for month_file_nm in monthly_files:
        print('\nUsing {}'.format(month_file_nm))
        season_of_file = what_season(month_file_nm)

        with cdms2.open(month_file_nm) as month_file:
            # For each variable in the month_file, add the data for this variable
            # to the appropriate output file
            for var in variables:
                var_data = month_file(var)
                for season in seasons:
                    # Don't want to get climo for monthly files that don't have the data
                    if season == season_of_file:
                        print('Creating climo for {} {}'.format(var, season))
                        climo = cdutil_seasons[season].climatology(var_data)
                        output_vars[s] += climo
                        #print('{}: {}'.format(season, climo.shape))
                '''
                data = month_file(var)
                out_file = output_files[i]
                out_file.write(data)
                '''

    # Write all of the files
    for s in seasons:
        # ex: 20180129.DECKv1b_piControl.ne30_oEC.edison_MAM_016603_017005_climo.nc
        case = '20180129.DECKv1b_piControl.ne30_oEC.edison'
        fnm = '{}_{}_{}01_{}12_climo.nc'.format(case, s, start_year, end_year)
        fnm = os.path.join(output_dir, fnm)
        print('Writing climo file: {}'.format(fnm))
        with cdms2.open(fnm, 'w') as f:
            f.write(output_vars[s])

    print('Done creating climo!')

    # Questions:
    # How to add variables of different shape to the climo?
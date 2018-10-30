# Table of Contents
1. [Problem](README.md#problem)
2. [Related Files](README.md#related-files)
3. [Run Instructions](README.md#run-instructions)
4. [Approaches](README.md#approaches)

# Problem

A newspaper editor was researching immigration data trends on H1B(H-1B, H-1B1, E-3) visa application processing over the past years, trying to identify the occupations and states with the most number of approved H1B visas. She has found statistics available from the US Department of Labor and its [Office of Foreign Labor Certification Performance Data](https://www.foreignlaborcert.doleta.gov/performancedata.cfm#dis). But while there are ready-made reports for [2018](https://www.foreignlaborcert.doleta.gov/pdf/PerformanceData/2018/H-1B_Selected_Statistics_FY2018_Q4.pdf) and [2017](https://www.foreignlaborcert.doleta.gov/pdf/PerformanceData/2017/H-1B_Selected_Statistics_FY2017.pdf), the site doesn’t have them for past years.

As a data engineer, you are asked to create a mechanism to analyze past years data, specifically calculate two metrics

This project being able to analyze data and calculate two metrics: **Top 10 Occupations** and **Top 10 States** for **certified** visa applications. And the code is reusable for future data.

# Related Files

The whole structure obey the required Repo directory structure.

- `./input/`includes datasets, since the data files are large, we neglect it by setting .gitignore.
- `./src/` includes source file `h1b_ayalysis.py`, the class `H1bAnalysor` makes the code being able to invoke easily in new situations for new datas.
- `./output/` includes results of analyzation, which includes **Top 10 Occupations** and **Top 10 States**.
- `./run.sh` we could write the commend here to execute the code with some arguments, which will be explained in detail later.

**Datasets**:

Raw data could be found [here](https://www.foreignlaborcert.doleta.gov/performancedata.cfm) under the __Disclosure Data__ tab (i.e., files listed in the __Disclosure File__ column with ".xlsx" extension).

This project being able to accept input from format give in Google drive [folder](https://drive.google.com/drive/folders/1Nti6ClUfibsXSQw5PUIWfVGSIrpuwyxf?usp=sharing).

The code being able to extract appropriate field values from 2014-2016 automatically.
For other years' date, especially when some field's name are different, we need user to set the `column_id` manually.

# Run Instructions

> python h1b_ayalysis.py path_to_input path_to_output_occ path_to_output_states

To use current program entrance, we need 3 more arguments given in order, the input file followed by 2 output file for top occupations and states respectively.

Since the main code for analyzation is wrapped as a class `H1bAnalysor`, it could be easily reused to write new code for new data and situations.

Here it support some functions and interfaces.

1. Instantiation and support printing runtime information on screen:

`H1bAnalysor(data_source, verbose=False)`, by setting `verbose` as True we could get information like:
- Whether there is any column with invalid format
- Current progresses

2. Indicate index of target field for new data format:

Since the field name could be different for different year, in default, the code could recognize 2014-2016 years' H1B data format automatically. For new format, we could use `def set_index(self, total_column, case_status, worksite_state, soc_code, soc_name)`, the parameters are index of fields we care for this analyzation.

3. Execute analyzation:

Invoke `def analysis(self)`, the `analysor` instance will start the analyzation.

4. Write the results to file:

we have `def get_occupations_result(self, out_file, top_size)` and `def get_states_result(self, out_file, top_size)` for this purpose.

*Using these functions other engineers could reuse the code.*

# Approaches

This section, we tell more about the details of the logic in the codes.

The general idea is this:

1. Extract related information
  - Significant Fields: status (e.g. 'CERTIFIED'), worksite_state (e.g. 'CA'), soc_code, soc_name (job category and name)
  - Concerns:
    - How to separate fields?
      - Could not use stand library function `split(';')` since some field values are string contain ';' symbol.
      - So we implemented a private function `_split_line(string)`, using sliding windows to separate fields.
    - More than 54 states?
      - Some states code don't belong to USA but only appears a small number number of time, so we just ignore them.
    - How to categorize of occupations?
      - The data are according to **Standard Occupational Classification** (SOC), and `soc_code` should work as the key, since the `soc_name` varies in same category.
      - Some `soc_code` are invalid, we need to infer the most possible correct one using `_validate_soc_code(soc_code, soc_name)`.
      - Here we select the first name used for the job category and use a map to store the code and name.
      - If allowed, we could use the SOC code book to build the name mapping.
2. Counting

To count efficiently, this project use Counter from collections, and as said before, here use `worksite_states` and `soc_code` as  key.

3. Find top 10 according to the order

Here this project uses a window of size 10, then implement the finding of top 10 in $O(n)$ time complexity, where $n$ is the size of counter. It was implemented in `_get_top10_states(size)` and `_get_top10_occ(size)`.

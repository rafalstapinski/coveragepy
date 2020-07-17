# coding: utf-8
# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Json reporting for coverage.py"""
import datetime
import json
import sys

from coverage import __version__
from coverage.report import get_analysis_to_report
from coverage.results import Numbers

from coverage.html import HtmlDataGeneration


class JsonReporter(object):
    """A reporter for writing JSON coverage results."""

    def __init__(self, coverage, return_data=False):
        self.coverage = coverage
        self.config = self.coverage.config
        self.total = Numbers()
        self.report_data = {}

        self.return_data = return_data

        self.datagen = HtmlDataGeneration(self.coverage)

    def report(self, morfs, outfile=None):
        """Generate a json report for `morfs`.

        `morfs` is a list of modules or file names.

        `outfile` is a file object to write the json to

        """

        outfile = outfile or sys.stdout
        coverage_data = self.coverage.get_data()
        coverage_data.set_query_contexts(self.config.report_contexts)
        self.report_data["meta"] = {
            "version": __version__,
            "timestamp": datetime.datetime.now().isoformat(),
            "branch_coverage": coverage_data.has_arcs(),
            "show_contexts": self.config.json_show_contexts,
        }

        measured_files = {}
        called_functions = set()

        for file_reporter, analysis in get_analysis_to_report(self.coverage, morfs):

            definitions = []

            file_data = self.datagen.data_for_file(file_reporter, analysis)

            namespace = []

            # previous_depth = 0
            # depth = 0

            INDENTATION_DEPTH = 4  # idk figure this out later

            for lineno, ldata in enumerate(file_data.lines, 1):

                token_types = [t[0] for t in ldata.tokens]
                token_names = [t[1] for t in ldata.tokens]

                if len(token_types) == 0:
                    continue

                depth = 0

                # get depths
                if token_types[0] == "ws":
                    _, indentation = token_types.pop(0), token_names.pop(0)

                    # dont update depths if remainder is empty line
                    if len(token_types) == 0:
                        continue

                    depth = int(len(indentation) / INDENTATION_DEPTH)

                if token_types[0] == "key" and token_names[0] == "async":
                    token_types = token_types[2:]
                    token_names = token_names[2:]

                # if definition
                if token_types[0] == "key" and token_names[0] in ("def", "class"):

                    definition_name = token_names[2]

                    if depth > (len(namespace) + 1):
                        namespace.append(definition_name)

                    elif depth == (len(namespace) + 1):
                        if len(namespace) == 0:
                            namespace.append(definition_name)
                        else:
                            namespace[-1] = definition_name

                    else:
                        namespace = namespace[:depth]
                        namespace.append(definition_name)

                    module_path = "{}::{}".format(
                        file_reporter.relative_filename(), "::".join(namespace)
                    )

                    definitions.append((lineno, module_path))

            file_report = self.report_one_file(coverage_data, analysis)

            definitions = list(sorted(definitions, key=lambda d: d[0], reverse=True))
            for executed_line in file_report["executed_lines"]:
                called_function = next(
                    d[1] for d in definitions if d[0] < executed_line
                )
                called_functions.add(called_function)

            measured_files[file_reporter.relative_filename()] = file_report

        self.report_data["executed_modules"] = list(called_functions)

        self.report_data["files"] = measured_files

        self.report_data["totals"] = {
            "covered_lines": self.total.n_executed,
            "num_statements": self.total.n_statements,
            "percent_covered": self.total.pc_covered,
            "missing_lines": self.total.n_missing,
            "excluded_lines": self.total.n_excluded,
        }

        if coverage_data.has_arcs():
            self.report_data["totals"].update(
                {
                    "num_branches": self.total.n_branches,
                    "num_partial_branches": self.total.n_partial_branches,
                    "covered_branches": self.total.n_executed_branches,
                    "missing_branches": self.total.n_missing_branches,
                }
            )

        if self.return_data:
            return self.report_data

        json.dump(
            self.report_data,
            outfile,
            indent=4 if self.config.json_pretty_print else None,
        )

        return self.total.n_statements and self.total.pc_covered

    def report_one_file(self, coverage_data, analysis):
        """Extract the relevant report data for a single file"""
        nums = analysis.numbers
        self.total += nums
        summary = {
            "covered_lines": nums.n_executed,
            "num_statements": nums.n_statements,
            "percent_covered": nums.pc_covered,
            "missing_lines": nums.n_missing,
            "excluded_lines": nums.n_excluded,
        }
        reported_file = {
            "executed_lines": sorted(analysis.executed),
            "summary": summary,
            "missing_lines": sorted(analysis.missing),
            "excluded_lines": sorted(analysis.excluded),
        }
        if self.config.json_show_contexts:
            reported_file["contexts"] = analysis.data.contexts_by_lineno(
                analysis.filename,
            )
        if coverage_data.has_arcs():
            reported_file["summary"].update(
                {
                    "num_branches": nums.n_branches,
                    "num_partial_branches": nums.n_partial_branches,
                    "covered_branches": nums.n_executed_branches,
                    "missing_branches": nums.n_missing_branches,
                }
            )
        return reported_file

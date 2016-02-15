import argparse
import arrow
import codecs
import datetime
import ics
import itertools
import pyparsing as pp
import re

from collections import defaultdict


def _group(s, groups):
  """Group a string using regex groups.

  Args:
      s: the string to group
      groups: a list of tuples of (regex pattern, replacement string)
  Returns:
      the group for the string
  """
  for pattern, replacement in groups:
    if pattern.match(s):
      return replacement
  return s


def _total_hours(seconds):
  """Converts seconds to hours.

  Args:
      seconds: the total seconds
  Returns:
      the total hours as a float
  """
  return seconds / 3600.0


def _parse_regexes(regexes):
  """Parses regexes in the form of '/from/to/options'.

  Note: this doesn't handle regex patterns

  Args:
      regexes: a list of regex strings
  Returns:
      a list of (regex pattern, replacement string)
  """
  regexBNF = (pp.Literal('/').suppress() +
              pp.Word(pp.printables + ' \t\n\r', excludeChars='/') +
              pp.Literal('/').suppress() +
              pp.Word(pp.printables + ' \t\n\r', excludeChars='/') +
              pp.Optional(pp.Literal('/').suppress() +
                          pp.ZeroOrMore(pp.Literal('i') ^
                                        pp.Literal('L') ^
                                        pp.Literal('s') ^
                                        pp.Literal('u') ^
                                        pp.Literal('x'))) +
              pp.StringEnd())
  results = []
  for regex in regexes:
    try:
      parsed = regexBNF.parseString(regex)
    except pp.ParseException as e:
      print('Unable to parse regex {0}'.format(regex))
      raise e
    regex_str = parsed[0]
    replace_str = parsed[1]
    if len(parsed) > 2:
      regex_str = '(?{0}){1}'.format(''.join(parsed[2:]), regex_str)
    print('Replacing {0} with {1}'.format(regex_str, replace_str))
    results.append((re.compile(regex_str), replace_str))
  return results


def _process_calendar(calendar_file,
                     start_date,
                     end_date,
                     allday,
                     grouping_regex_strs):
  """Processes a calendar, grouping events by name.

  Args:
      calendar_file: the ics calendar file
      start_date: the starting date, or None
      end_date: the end date, or None
      allday: if true, includes all day events in processing
      grouping_regex_strs: regular expressions for grouping patterns
  """
  print('Processing events from {0} to {1}'.format(start_date, end_date))
  regexes = _parse_regexes(grouping_regex_strs)
  calendar = ics.Calendar(calendar_file)
  groups = defaultdict(lambda: 0)
  total_seconds = 0
  for event in calendar.events:
    if not allday and event.all_day:
      continue
    if start_date and arrow.get(event.begin) < start_date:
      continue
    if end_date and arrow.get(event.end) > end_date:
      continue
    total_seconds += event.duration.total_seconds()
    event_name = _group(event.name, regexes)
    groups[event_name] += event.duration.total_seconds()

  for name, duration in sorted(groups.items(),
                               key=lambda item: item[1],
                               reverse=True):
    print('{0}: {1}'.format(name, _total_hours(duration)))


def _valid_date(s):
  """Validates and converts a date as arrow-compatible.

  Args:
      s: the string argument
  Returns:
      an arrow date
  Raises:
      ArgumentTypeError: if the date is invalid
  """
  try:
    return arrow.get(s)
  except TypeError:
    msg = "Not a valid date: '{0}'.".format(s)
    raise argparse.ArgumentTypeError(msg)


def main():
  parser = argparse.ArgumentParser(
    description='Analyzes calendar events to track time spent on activities.')
  parser.add_argument('-s',
                      '--startdate',
                      help=('the start date, inclusive '
                            '(ISO-8601 compliant, i.e. YYYY-MM-DD)'),
                      type=_valid_date)
  parser.add_argument('-e',
                      '--enddate',
                      help=('the end date, exclusive '
                            '(ISO-8601 compliant, i.e. YYYY-MM-DD)'),
                      type=_valid_date)
  parser.add_argument('-c',
                      '--calendar',
                      help='the calendar file (.ics)',
                      type=argparse.FileType('r', encoding='iso-8859-1'),
                      required=True)
  parser.add_argument('--allday',
                      help='include all day events',
                      type=bool,
                      default=False)
  parser.add_argument('regexes',
                      metavar='N',
                      type=str,
                      nargs='*',
                      help=('regular expressions to group events by. '
                            'These are of the form /toReplace/replaceWith/ '
                            'Optionally, regex flags can be passed after the '
                            'last slash. For example, for case insensitive '
                            'matching, pass /toReplace/replaceWith/i'))
  args = parser.parse_args()
  return _process_calendar(args.calendar,
                           args.startdate,
                           args.enddate,
                           args.allday,
                           args.regexes)

main()

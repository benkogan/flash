#!/usr/bin/env ruby

require "optparse"
require "json"

class Flash
  VERSION = [0, 0, 2]

  def main
    options = Options.parse ARGV
    collection = Collection.new(options.collection_path)

    if options.command = 'add'
      Screen.with_screen do |screen, tty|
        Add.run_in_screen(collection, options.unit, screen, tty)
      end
    elsif options.command = 'review'
      search = Search.parse(options.query)
      notes = collection.filter_by(search)
      cards = collection.build_cards(notes)
      Screen.with_screen do |screen, tty|
        Quiz.new(options.mode).run_in_screen(cards, screen, tty)
      end
    end
  end

end

class Add

  def self.run_in_screen(collection, unit, screen, tty)
    # add unit to collection
    # pass to event loop? or use event loop block?
  end

  def self.ui_event_loop
  end

end

class Options
  def self.parse(argv)
    options = OpenStruct.new
    options.collection_path = nil
    options.query = nil
    options.mode = :srs
    options.unit = nil
    options.command = nil

    global = OptionParser.new do |opts|
      opts.banner = "Usage: #{$PROGRAM_NAME} [options] [commands]"

      opts.on_tail("-h", "--help", "Show this message") do |v|
        puts opts
        puts
        puts "TODO: commands list"
        puts "TODO: how to get help for each command (command -h"
        exit
      end

      opts.on_tail("-v", "--version", "Show version") do
        puts Flash::VERSION.join('.')
        exit
      end
    end

    subcommands = {
      "review" => OptionParser.new do |opts|
        opts.banner = command_banner("review")

        opts.on("-qQUERY", "--query=QUERY", "Search for units and tags") do |q|
          options.query = q
        end

        opts.on("--cram", "Toggle cram review mode (default)") do |o|
          options.mode = :cram
        end

        opts.on("--srs", "Toggle SRS review mode") do |o|
          options.mode = :srs
        end

        opts.on_tail("-h", "--help", "Show this message") do |v|
          puts opts
          exit
        end
      end,

      "add" => OptionParser.new do |opts|
        opts.banner = command_banner("add")

        opts.on("-uUNIT", "--unit=UNIT", "Specify unit to add to") do |u|
          options.unit = u
        end

        opts.on_tail("-h", "--help", "Show this message") do |v|
          puts opts
          exit
        end
      end
    }

    begin
      global.order!
      subcommand = argv.shift
      options.command = subcommand
      options.collection_path = argv.shift
      subcommands[subcommand].order!
    rescue OptionParser::InvalidOption => e
      $stderr.puts e
      $stderr.puts global
      exit 1
    end

    options
  end

  def self.command_banner(subcommand)
    "Usage: #{$PROGRAM_NAME} #{subcommand} [options]"
  end
end

class Search
  # TODO: what if query is empty
  def self.parse(query)
    begin
      query_atoms = query.split
      query_atoms.map { |atom| parse_query_atom atom }
    rescue InvalidQueryAtomError => e
      $stderr.puts e
      exit 1
    end
  end

  # Valid searches include:
  #   => unit
  #   => unit[tag]
  #   => unit[tag1,tag2,tag3]

  def self.parse_query_atom(atom)
    unit_symb = '(?<unit>\w+)'
    tags_symb = '(?<tags>\w+(?:,\w+)*)'
    atom_symb = /^#{unit_symb}(?:\[#{tags_symb}\])?$/

    matched = atom_symb.match(atom)
    raise InvalidQueryAtomError if matched.nil?

    OpenStruct.new(
      unit: matched[:unit],
      tags: matched[:tags] ? matched[:tags].split(',') : nil
    )
  end

  class InvalidQueryAtomError < RuntimeError; end
end

class Collection
  def initialize(file_path)
    @path = file_path
    @data = File.read(@path)
    @json = JSON.parse(@data)

    @definition = @json.fetch('definition')
    @notes = @json.fetch('notes')
  end

  # TODO: what if filter returns nothing?
  # NOTE: if no tags specified for a group, returns all notes
  def filter_by(search_groups)
    filtered_notes = search_groups.map do |group|
      if group.tags
        filter_by_tag(@notes[group.unit], group.tags)
      else
        @notes[group.unit]
      end
    end
    filtered_notes.flatten
  end

  def filter_by_tag(notes, tags)
    notes.select do |note|
      intersection?(tags, note["tags"])
    end
  end

  def intersection?(first, second)
    overlap = second.select { |x| first.include? x }
    overlap.any?
  end

  def build_cards(notes)
    cards = notes.map do |note|
      @definition.map do |ordering_style, sides|
        build_card(sides, note)
      end
    end
    cards.flatten
  end

  def build_card(sides, note)
    sides = sides.map do |side|
      side.map do |key|
        # new fact
        OpenStruct.new(
          key: key,
          val: note[key]
        )
      end
    end
    Card.new(sides)
  end
end

class Card
  def initialize(sides)
    @sides = sides
  end
end

class Renderer
end

class Screen
end

class ANSI
end

class TTY
end

Flash.new.main if $0 == __FILE__


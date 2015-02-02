require "json"

class Flash
  def main
    # . . .

    options = Configuration.parse_options(ARGV) # TODO

    search_groups = Configuration.parse_search(options[:query])
    collection = Collection.new(file_path).load # TODO
    notes = collection.filter(search_groups) # TODO
    cards = Collection.build_cards(notes) # TODO

    # . . .
    cards
  end

  def quiz
  end
end

class Configuration

  def self.parse_search(query)
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
    word_symb = '\w+'
    tags_symb = '\[(\w+(?:,\w+)*)\]'

    unit_pattern = /#{word_symb}/
    tags_pattern = /#{tags_symb}/
    query_pattern = /^#{word_symb}(?:#{tags_symb})?$/

    raise InvalidQueryAtomError if query_pattern.match(atom).nil?

    unit = unit_pattern.match(atom)
    tags = tags_pattern.match(atom)

    # extract data if there are matches
    unit = unit.to_a.pop if unit
    tags = tags[1].split(',') if tags

    {unit: unit, tags: tags}
  end

  class InvalidQueryAtomError < RuntimeError; end

end

class Collection

  def initialize(file_path)
    @file_path = file_path
  end

  def load
    collection_file = file.load @file_path
    collection_file # TODO
  end

  def filter(search_groups)
  end

end

class Card
end

class Renderer
end

class Screen
end

class ANSI
end

class TTY
end


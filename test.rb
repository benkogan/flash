require_relative "flash"
require "minitest/autorun"

describe Search do
  describe "#parse_query_atom" do
    it "must parse a unit" do
      group = Search.parse_query_atom 'unit'
      group[:unit].must_equal 'unit'
    end

    it "must parse a unit before a tag" do
      group = Search.parse_query_atom 'unit[a]'
      group[:unit].must_equal 'unit'
    end

    it "must parse a unit and single tag" do
      group = Search.parse_query_atom 'unit[a]'
      group[:tags].must_equal ['a']
    end

    it "must parse a unit and multiple tags" do
      group = Search.parse_query_atom 'unit[a,b,c]'
      group[:tags].must_equal ['a', 'b', 'c']
    end

    it "must complain about bogus atoms" do
      bogus_query_atoms = ['test[', '[a]', '[a,b]', ']a&dsf[$&adsf^,ds,[]']
      bogus_query_atoms.each do |atom|
        assert_raises(Search::InvalidQueryAtomError) do
          Search.parse_query_atom atom
        end
      end
    end
  end

  describe "#parse" do
    it "must parse a query" do
      search = Search.parse 'u1 u2[a,b,c]'

      group = search.shift
      group.unit.must_equal "u1"
      group.tags.must_be_nil

      group = search.shift
      group.unit.must_equal "u2"
      group.tags.must_equal ["a", "b", "c"]
    end
  end
end

describe Collection do
end


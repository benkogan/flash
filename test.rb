require_relative "flash"
require "minitest/autorun"

describe Configuration do

  describe "#parse_query_atom" do

    it "must parse a unit" do
      group = Configuration.parse_query_atom 'unit'
      group[:unit].must_equal 'unit'
    end

    it "must parse a unit before a tag" do
      group = Configuration.parse_query_atom 'unit[a]'
      group[:unit].must_equal 'unit'
    end

    it "must parse a unit and single tag" do
      group = Configuration.parse_query_atom 'unit[a]'
      group[:tags].must_equal ['a']
    end

    it "must parse a unit and multiple tags" do
      group = Configuration.parse_query_atom 'unit[a,b,c]'
      group[:tags].must_equal ['a', 'b', 'c']
    end

    it "must complain about bogus atoms" do
      bogus_query_atoms = ['test[', '[a]', '[a,b]', ']a&dsf[$&adsf^,ds,[]']
      bogus_query_atoms.each do |atom|
        assert_raises(Configuration::InvalidQueryAtomError) do
          Configuration.parse_query_atom atom
        end
      end
    end

  end

  describe "#parse_query" do

    it "must parse a query" do
      search = Configuration.parse_search 'u1 u2[a,b,c]'
      search.must_equal [{:unit=>"u1", :tags=>nil}, {:unit=>"u2", :tags=>["a", "b", "c"]}]
    end

  end

end


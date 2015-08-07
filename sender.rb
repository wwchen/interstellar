require 'rest-client'
require 'json'
require 'date'
require 'csv'
require 'yaml'

CONFIG = YAML.load_file('./secrets/secrets.yml')

date = Date.today-2

file_date = date.strftime("%Y%m")
csv_file_name = "reviews_#{CONFIG["package_name"]}_#{file_date}.csv"

system "gs://#{CONFIG["app_repo"]}/reviews/#{csv_file_name} ."


class Slack
  def self.notify(message)
    RestClient.post CONFIG["slack_url"], {
      payload:
      { text: message }.to_json
    },
    content_type: :json,
    accept: :json
  end
end

class Review
  def self.collection
    @collection ||= []
  end

  def self.send_reviews_from_date(date)
    message = collection.select do |r|
      r.submitted_at > date && (r.title || r.text)
    end.sort_by do |r|
      r.submitted_at
    end.map do |r|
      r.build_message
    end.join("\n")


    if message != ""
      Slack.notify(message)
    else
      print "No new reviews\n"
    end
  end

  attr_accessor :text, :title, :submitted_at, :original_subitted_at, :rate, :device, :url, :version, :edited

  def initialize data = {}
    @text = data[:text] ? data[:text].to_s.encode("utf-8") : nil
    @title = data[:title] ? "*#{data[:title].to_s.encode("utf-8")}*\n" : nil

    @submitted_at = DateTime.parse(data[:submitted_at].encode("utf-8"))
    @original_subitted_at = DateTime.parse(data[:original_subitted_at].encode("utf-8"))

    @rate = data[:rate].encode("utf-8").to_i
    @device = data[:device] ? data[:device].to_s.encode("utf-8") : nil
    @url = data[:url].to_s.encode("utf-8")
    @version = data[:version].to_s.encode("utf-8")
    @edited = data[:edited]
  end

  def notify_to_slack
    if text || title
      # todo format submitted_at
      # todo show edited date if different
      message = "*Rating: #{rate}* | version: #{version} | #{submitted_at}\n #{[title, text].join(" ")}\n <#{url}|Ответить в Google play>"
      Slack.notify(message)
    end
  end

  def build_message
    date = if edited
             "subdate: #{original_subitted_at.strftime("%d.%m.%Y at %I:%M%p")}, edited at: #{submitted_at.strftime("%d.%m.%Y at %I:%M%p")}"
           else
             "subdate: #{submitted_at.strftime("%d.%m.%Y at %I:%M%p")}"
           end

    stars = rate.times.map{"★"}.join + (5 - rate).times.map{"☆"}.join

    [
      "\n\n#{stars}",
      "Version: #{version} | #{date}",
      "#{[title, text].join(" ")}",
      "<#{url}|Ответить в Google play>"
    ].join("\n")
  end
end

CSV.foreach(csv_file_name, encoding: 'bom|utf-16le', headers: true) do |row|
  # If there is no reply - push this review
  if row[11].nil?
    Review.collection << Review.new({
      text: row[10],
      title: row[9],
      submitted_at: row[6],
      edited: (row[4] != row[6]),
      original_subitted_at: row[4],
      rate: row[8],
      device: row[3],
      url: row[14],
      version: row[1],
    })
  end
end

Review.send_reviews_from_date(date)

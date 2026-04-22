#!/usr/bin/env ruby
# frozen_string_literal: true

require 'oj'
begin
  require 'prism'
  PRISM_AVAILABLE = true
rescue LoadError => e
  PRISM_AVAILABLE = false
  PRISM_ERROR = e.message
end

$stdout.sync = true

BRANCH_NODE_SUFFIXES = %w[
  IfNode
  UnlessNode
  WhileNode
  UntilNode
  ForNode
  CaseNode
  CaseMatchNode
  RescueNode
].freeze

def emit(payload)
  puts(Oj.dump(payload, mode: :compat))
end

def node_children(node)
  return [] unless node.respond_to?(:child_nodes)

  node.child_nodes.compact
end

def branch_node?(node)
  BRANCH_NODE_SUFFIXES.any? { |suffix| node.class.name.end_with?(suffix) }
end

def inherited_class?(node)
  return false unless node.class.name.end_with?('ClassNode')
  return false unless node.respond_to?(:superclass)

  !node.superclass.nil?
end

def traverse(node, metrics, depth = 0)
  metrics[:max_nesting_depth] = [metrics[:max_nesting_depth], depth].max

  class_name = node.class.name
  metrics[:method_definitions] += 1 if class_name.end_with?('DefNode')
  metrics[:inherited_classes] += 1 if inherited_class?(node)

  next_depth = depth
  if branch_node?(node)
    metrics[:branch_nodes] += 1
    next_depth += 1
  end

  node_children(node).each do |child|
    traverse(child, metrics, next_depth)
  end
end

def lore_line(entropy, violations, metrics)
  return 'The geometry is non-Euclidean here; recursion folds back into itself.' if metrics[:max_nesting_depth] >= 7
  return 'This class inherits from too many ancestors; the lineage is diluted.' if metrics[:inherited_classes] >= 3
  return 'Method sigils crowd the walls. Entropy has found a permanent chamber.' if metrics[:method_definitions] >= 20
  return 'Branching paths fork into shadow. The temple refuses a straight corridor.' if metrics[:branch_nodes] >= 14
  return "Ruff's crows circle overhead; this vault is drawing technical debt." if violations >= 12
  return 'The stone sweats sepia. Refactor before sunset.' if entropy >= 0.68

  'The archive breathes evenly. Keep the invariants fed.'
end

def heuristic_metrics(source)
  rough_depth = source.scan(/[{\[]/).length - source.scan(/[}\]]/).length
  {
    max_nesting_depth: [rough_depth, 0].max,
    method_definitions: source.scan(/\b(def|function|fn)\b/).length,
    inherited_classes: source.scan(/\b(class\s+\w+\s*<|extends\s+\w+)/).length,
    branch_nodes: source.scan(/\b(if|else|switch|case|while|for)\b/).length
  }
end

ARGF.each_line do |raw|
  line = raw.delete_prefix("\uFEFF").strip
  next if line.empty?

  begin
    payload = Oj.load(line, mode: :compat)
    unless payload['type'] == 'lore-request'
      emit(
        {
          type: 'error',
          source: 'ruby',
          message: "unknown request type: #{payload['type']}"
        }
      )
      next
    end

    root = payload.fetch('root')
    relative_path = payload.fetch('path')
    entropy = payload.fetch('entropy').to_f
    violations = payload.fetch('violations').to_i

    unless PRISM_AVAILABLE
      emit(
        {
          type: 'error',
          source: 'ruby',
          message: "prism unavailable: #{PRISM_ERROR}"
        }
      )
      next
    end

    absolute_path = File.expand_path(relative_path, root)
    source = File.read(absolute_path, encoding: 'utf-8')
    parse_result = Prism.parse(source)
    metrics = if parse_result.errors.empty?
                parsed = {
                  max_nesting_depth: 0,
                  method_definitions: 0,
                  inherited_classes: 0,
                  branch_nodes: 0
                }
                traverse(parse_result.value, parsed)
                parsed
              else
                heuristic_metrics(source)
              end

    emit(
      {
        type: 'lore',
        root: root,
        path: relative_path,
        entropy: entropy,
        violations: violations,
        line: lore_line(entropy, violations, metrics),
        metrics: metrics,
        generatedAt: (Time.now.to_f * 1000).to_i
      }
    )
  rescue StandardError => e
    emit(
      {
        type: 'error',
        source: 'ruby',
        message: e.message
      }
    )
  end
end

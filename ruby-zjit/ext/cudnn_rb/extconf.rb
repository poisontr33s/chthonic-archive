require 'mkmf'

# cudnn_rb — cuDNN version + handle availability probe
# cuDNN v9.x header layout: CUDNN_PATH/include/<cuda-ver>/cudnn.h (versioned subdir)
# cuDNN v8.x / system packages: flat CUDNN_PATH/include/cudnn.h
# Both layouts handled via ordered candidate path search.

cuda_base = ENV['CUDA_PATH'] ||
            (Dir.exist?('/usr/local/cuda') ? '/usr/local/cuda' : nil) ||
            Dir.glob('/usr/local/cuda-*').sort.last ||
            '/usr/local/cuda'

cudnn_base = ENV['CUDNN_PATH'] || ''

# Win32: glob latest cuDNN SDK install (version-agnostic)
if cudnn_base.empty? && RUBY_PLATFORM =~ /mswin|mingw/
  candidate = Dir.glob('C:/Program Files/NVIDIA/CUDNN/v*').sort.last
  cudnn_base = candidate if candidate && Dir.exist?(candidate)
end

# Assemble candidate include dirs — cuDNN v9.x has versioned subdir
cudnn_inc_dirs = []
unless cudnn_base.empty?
  # v9.x: include/<cuda-major>.x/cudnn.h — glob all versioned subdirs
  Dir.glob("#{cudnn_base}/include/*/cudnn.h").each do |h|
    cudnn_inc_dirs << File.dirname(h)
  end
  cudnn_inc_dirs << "#{cudnn_base}/include"   # v8.x flat fallback
end
# CUDA toolkit ships cudnn.h alongside CUDA headers on some installs
cudnn_inc_dirs << "#{cuda_base}/include"
cudnn_inc_dirs << '/usr/include'
cudnn_inc_dirs.uniq!

$INCFLAGS += cudnn_inc_dirs.map { |d| " -I#{d}" }.join

$LIBPATH = [
  ("#{cudnn_base}/lib/x64"             unless cudnn_base.empty?),
  ("#{cudnn_base}/lib64"               unless cudnn_base.empty?),
  ("#{cudnn_base}/lib"                 unless cudnn_base.empty?),
  "#{cuda_base}/lib64",
  "#{cuda_base}/lib/x64",
  '/usr/lib64',
  '/usr/lib/x86_64-linux-gnu',
].compact + $LIBPATH

$LOCAL_LIBS += ' -lcudart -lcudnn'

unless find_header('cudnn.h', *cudnn_inc_dirs)
  abort "Cannot find cudnn.h — install cuDNN devel package or set CUDNN_PATH\n" \
        "cuDNN v9.x: headers at CUDNN_PATH/include/<cuda-ver>/cudnn.h"
end

create_makefile('cudnn_rb')

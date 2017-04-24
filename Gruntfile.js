module.exports = grunt => {
  // load all grunt tasks matching the ['grunt-*', '@*/grunt-*'] patterns
  require('load-grunt-tasks')(grunt, {scope: 'devDependencies'});

  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),

    shell: {
      loadapp: {
          command: function(app) {
              return '/usr/local/bin/docker exec -t juicebox bash -c "python manage.py loadjuiceboxapp ' + app + '" || echo "\nFailed!"'
          }
      },
      makejs: {
        command: '/usr/local/bin/docker exec -t juicebox bash -c "make js collectstatic"'
      },
    },

    watch: {
      grunt: {
        options: {
          reload: true,
          spawn: false,
          debounceDelay: 2000
        },
        files: ['Gruntfile.js'],
      },

      apps: {
        files: [
            'apps/**/*.yaml',
            'apps/**/*.json',
            'apps/**/*.png',
            'apps/**/*.jpg',
            'apps/**/*.gif',
            'apps/**/*.md',
            'apps/**/*.html',
        ],
        options: {
          spawn: false,
        }
      },

      js: {
        files: [
            'public/js/src/**/*',
            'public/test/js/spec/v3/**/*'
        ],
        tasks: ['shell:makejs'],
        options: {
          spawn: false,
        }
      },
    }
  });

  grunt.event.on('watch', function(action, filepath, target) {
      if (target == 'apps') {
        app = filepath.split('/')[1];
        grunt.log.writeln('App ' + app + ' modified. Reloading');
        grunt.task.run('shell:loadapp:' + app);
      }
  });
};

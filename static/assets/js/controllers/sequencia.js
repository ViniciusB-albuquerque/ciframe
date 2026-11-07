angular.module('deciframeApp').controller('SequenciaController', function($http, $window, ngProgressFactory, $anchorScroll, $location, GENEROS) {
  var COR_PADRAO = '#2E1C74';

  var formatarAcorde = function(acorde) {
    return acorde.charAt(0).toUpperCase() + acorde.slice(1);
  };

  var criarSequencia = function(item) {
    var acordes = item.acordes ? item.acordes.split(';') : [];
    return {
      'id': item.id,
      'nome': item.nome,
      'chave': item.chave,
      'acordes': acordes.map(function(acorde) {
        return { 'acorde': formatarAcorde(acorde), 'cor': COR_PADRAO };
      })
    };
  };

  var vm = this;
  vm.sequenciasFamosas = [];
  vm.carregandoSequencias = false;
  vm.erroSequencias = "";
  vm.minhaSequencia = {};
  vm.novaSequencia = { 'nome': "", 'acordes': "" };
  vm.cadastrando = false;
  vm.erroCadastro = "";
  vm.mensagemCadastro = "";
  vm.isSearching = false;
  vm.showSearchResultsCount = false;
  vm.esfigeSpeech = "";
  vm.musics = [];
  vm.generos = GENEROS;
  vm.meuGenero = "";
  vm.generoEscolhido = false;
  vm.progressbar = ngProgressFactory.createInstance();

  vm.carregarSequencias = function() {
    vm.carregandoSequencias = true;
    vm.erroSequencias = "";
    $http.get("sequencias")
      .success(function(data) {
        vm.sequenciasFamosas = data.map(criarSequencia);
        vm.carregandoSequencias = false;
      })
      .error(function() {
        vm.erroSequencias = "Não foi possível carregar o catálogo de sequências.";
        vm.carregandoSequencias = false;
      });
  };

  vm.cadastrarSequencia = function() {
    vm.erroCadastro = "";
    vm.mensagemCadastro = "";
    var acordes = (vm.novaSequencia.acordes || "").trim();
    if (!acordes) {
      vm.erroCadastro = "Informe ao menos um acorde.";
      return;
    }
    vm.cadastrando = true;
    $http.post("sequencias", {
      'nome': (vm.novaSequencia.nome || "").trim(),
      'acordes': acordes
    })
      .success(function() {
        vm.cadastrando = false;
        vm.novaSequencia = { 'nome': "", 'acordes': "" };
        vm.mensagemCadastro = "Sequência cadastrada.";
        vm.carregarSequencias();
      })
      .error(function(data) {
        vm.cadastrando = false;
        vm.erroCadastro = (data && data.erro) ? data.erro : "Não foi possível cadastrar a sequência.";
      });
  };

  vm.temAcorde = function(acorde) {
    if (vm.minhaSequencia.acordes) {
      return (vm.minhaSequencia.acordes.indexOf(acorde) > -1);
    } else {
      return false;
    }
  }

  var createChordsString = function(chords) {
    var str = "";
    for (var i = 0; i < chords.length; i++) {
      str = str.concat(chords[i].acorde, ',');
    }
    return str.substring(0, str.length-1);
  }

  vm.pesquisarPorSequencia = function(sequencia) {
    if (sequencia) {
      vm.minhaSequencia = sequencia;
    }
    vm.progressbar.start();
    vm.esfigeSpeech = "Procurando músicas com base na sequencia...";
    vm.isSearching = true;
    vm.musics = [];

    var apiUrl = "";
    var searchString = "similares?sequencia=".concat(createChordsString(vm.minhaSequencia.acordes));
    if (vm.generoEscolhido && vm.meuGenero) {
      searchString += "&generos="+vm.meuGenero;
    }
    $http.get(apiUrl.concat(searchString))
      .success(function(data) {
        vm.progressbar.complete();
        vm.esfigeSpeech = "Encontrei essas músicas";
        vm.isSearching = false;
        vm.showSearchResultsCount = true;
        vm.musics = data;
      })
      .error(function(data) {
        vm.esfigeSpeech = "Ops! Algo errado.";
        vm.isSearching = false;
        vm.showSearchResultsCount = false;
      });
  }

  vm.aoEscolherGenero = function() {
    vm.generoEscolhido = !!vm.meuGenero;
    if (vm.minhaSequencia.acordes) {
      vm.pesquisarPorSequencia();
    }
  }

  vm.limparPesquisa = function() {
    vm.minhaSequencia = {};
    vm.musics = [];
  }

  vm.goToLirics = function(music) {
    $window.open(music.url);
  };

  vm.goToResults = function() {
    vm.showSearchResultsCount = false;
    $("body").animate({scrollTop: $("#results").offset().top}, "slow");
  };

  vm.carregarSequencias();
});

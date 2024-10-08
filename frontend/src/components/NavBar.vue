<template>
    <nav class="navbar">
        <div class="title"> <RouterLink to="/overview" @click="resetMenu">價格追蹤小幫手</RouterLink></div>
        <div :class="{ 'hamburger': !menuVisible, 'hamburger-dark' : menuVisible}" @click="toggleMenu">
          <div class="bar"></div>
          <div class="bar"></div>
          <div class="bar"></div>
        </div>
        <ul class="options" :class="{ 'show-menu': menuVisible }">
            <li><RouterLink to="/overview" @click="resetMenu">物價概覽</RouterLink></li>
            <li><RouterLink to="/trending" @click="resetMenu">物價趨勢</RouterLink></li>
            <li><RouterLink to="/news" @click="resetMenu">相關新聞</RouterLink></li>
            <li v-if="!isLoggedIn"><RouterLink to="/login" @click="resetMenu">登入</RouterLink></li>
            <li v-else @click="logout">Hi, {{getUserName}}! 登出</li>
        </ul>
    </nav>
</template>

<script>
import { useAuthStore } from '@/stores/auth';

export default {
  name: 'NavBar',
  components: {},
  data() {
    return {
      menuVisible: false
    };
  },
    computed: {
        isLoggedIn(){
            const userStore = useAuthStore();
            return userStore.isLoggedIn;
        },
        getUserName(){
            const userStore = useAuthStore();
            return userStore.getUserName;
        }
    },
    methods: {
        logout(){
            this.resetMenu();
            const userStore = useAuthStore();
            userStore.logout();
        },
        toggleMenu(){
            this.menuVisible = !this.menuVisible;
        },
        resetMenu(){
            this.menuVisible = false;
        }
    }
};
</script>

<style scoped>
.navbar {
  display: flex;
  justify-content: space-between;
  background-color: #f3f3f3;
  padding: 1.5em;
  height: 4.5em;
  width: 100%;
  align-items: center;
  box-shadow: 0 0 5px #000000;
}

.hamburger {
  display: none;
  cursor: pointer;
  flex-direction: column;
  justify-content: space-around;
  height: 2.3em;
  border: 1px solid #333;
  border-radius: 10px;
  padding: 8px;
}

.hamburger-dark {
  display: none;
  cursor: pointer;
  flex-direction: column;
  justify-content: space-around;
  background-color: black;
  height: 2.3em;
  border: 1px solid #333;
  border-radius: 10px;
  padding: 8px;
}

.hamburger .bar {
  width: 20px;
  height: 2px;
  background-color: #333;
  margin: 2px 0;
}

.hamburger-dark .bar {
  width: 20px;
  height: 2px;
  background-color: #ffffff;
  margin: 2px 0;
}

.navbar ul {
  list-style: none;
  display: flex;
  justify-content: space-around;
}

.navbar li {
  color: #575B5D;
  margin: 0 .5em;
  font-size: 1.2em;
}

.navbar li:hover {
  cursor: pointer;
  font-weight: bold;
}

@media only screen and (max-width: 600px) {
  .navbar ul {
    display: none;
  }

  .navbar li {
    padding-top: 10px;
    padding-bottom: 10px;
    border-bottom: 1px solid #797979;
  }
  .navbar li:last-child {
    border-bottom: none;
  }

  .navbar ul.show-menu {
    display: flex;
    flex-direction: column;
    position: absolute;
    top: 4.5em;
    left: 0;
    width: 100%;
    background-color: #f3f3f3;
    box-shadow: 0 0 5px #000000;
  }
  .hamburger {
    display: flex;
  }

  .hamburger-dark {
    display: flex;
  }
}

.title > a {
  font-size: 1.4em;
  font-weight: bold;
  color: #2c3e50 !important;
}

.navbar a {
  text-decoration: none;
  color: #575B5D;
}
</style>
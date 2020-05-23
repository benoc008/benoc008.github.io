class TeacherComponent {

  connectionService;

  init() {
    this.connectionService.registerCallback(this.onMessage);
    this.connectionService.sendToAll('hello');
  }

  onMessage(message) {
    console.log(message);
  }
}
